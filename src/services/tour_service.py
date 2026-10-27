"""Query logic backing tour-level aggregates, such as ticket revenue."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, NamedTuple, Optional

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from ..config import MAX_ARTIST_SEARCH_RESULTS
from ..database import get_reference_time
from ..models import Concert, Tour, Venue
from ..schemas.tour import OCCUPANCY_PERCENTAGE_PRECISION, TourCityOut, TourOccupancySchema, TourStatus

# Not a `TourStatus` member: that enum is reserved for the statuses accepted
# by `GET /tours`'s `status` query filter, and "cancelled" isn't one of them
# (confirmed by `tests/test_tour_status_enum.py`). It's still a valid value
# for `Tour.status` itself, set directly by the cancel/uncancel tour flow.
CANCELLED_TOUR_STATUS = "cancelled"


class TourRevenue(NamedTuple):
    """Ticket revenue for a tour, and the count of concerts it was summed over."""

    revenue: Decimal
    concert_count: int


class TourNotFoundError(Exception):
    """Raised by `get_tour_span` when no tour with the given id exists."""


class TourConflictError(Exception):
    """Raised by `uncancel_tour` when the tour's status doesn't allow the
    requested transition (e.g. uncancelling a tour that isn't cancelled)."""


class TourSpan(NamedTuple):
    """A tour's date span, derived from its non-cancelled concerts."""

    first_date: Optional[date]
    last_date: Optional[date]
    days_between: Optional[int]


def get_tour_revenue(db: Session, tour_id: int) -> Optional[TourRevenue]:
    """Compute total ticket revenue for a tour, and the number of concerts
    it was summed over.

    Revenue is `sum(ticket_price * tickets_sold)` across the tour's
    non-cancelled concerts; cancelled concerts are excluded from both the
    revenue and the concert count. Returns `None` when no tour with
    `tour_id` exists, so the router can translate that into a 404.
    """
    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        return None

    revenue_total, concert_count = (
        db.query(
            func.coalesce(func.sum(Concert.ticket_price * Concert.tickets_sold), 0),
            func.count(Concert.id),
        )
        .filter(Concert.tour_id == tour_id, Concert.is_cancelled.is_(False))
        .first()
    )
    return TourRevenue(revenue=Decimal(revenue_total), concert_count=concert_count)


def get_tour_cities(db: Session, tour_id: int) -> Optional[List[TourCityOut]]:
    """Return the distinct cities a tour passes through, in date order,
    each paired with the date of its earliest non-cancelled concert.

    Cancelled concerts are excluded. When a city is visited more than once,
    its earliest concert date determines both its position and its
    `first_concert_date`. Returns `None` when no tour with `tour_id`
    exists, so the router can translate that into a 404.
    """
    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        return None

    rows = (
        db.query(Venue.city, func.min(Concert.date_time))
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Concert.tour_id == tour_id, Concert.is_cancelled.is_(False))
        .group_by(Venue.city)
        .order_by(func.min(Concert.date_time))
        .all()
    )

    return [
        TourCityOut(city=city, first_concert_date=first_date_time.date())
        for city, first_date_time in rows
    ]


def get_tour_span(tour_id: int, db: Session) -> TourSpan:
    """Compute a tour's date span from its non-cancelled concerts.

    `days_between` is the integer number of calendar days between
    `first_date` and `last_date` (0 when there's only one concert). Returns
    a `TourSpan` of all `None` when the tour has zero non-cancelled
    concerts. Raises `TourNotFoundError` when no tour with `tour_id`
    exists, so the router can translate that into a 404.
    """
    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        raise TourNotFoundError(f"Tour {tour_id} not found")

    first_date_time, last_date_time = (
        db.query(func.min(Concert.date_time), func.max(Concert.date_time))
        .filter(Concert.tour_id == tour_id, Concert.is_cancelled.is_(False))
        .first()
    )
    if first_date_time is None:
        return TourSpan(first_date=None, last_date=None, days_between=None)

    first_date = first_date_time.date()
    last_date = last_date_time.date()
    return TourSpan(
        first_date=first_date,
        last_date=last_date,
        days_between=(last_date - first_date).days,
    )


def get_tour_occupancy(db: Session, tour_id: int) -> Optional[TourOccupancySchema]:
    """Compute ticket occupancy for a tour, aggregated over its non-cancelled
    concerts.

    `tickets_sold` and `total_capacity` are summed from `Concert.tickets_sold`
    and the linked `Venue.capacity` across the tour's non-cancelled concerts;
    cancelled concerts are excluded from both sums. `percentage_sold` is
    `tickets_sold / total_capacity * 100`, rounded to
    `OCCUPANCY_PERCENTAGE_PRECISION` decimal places, and is `0.0` (rather
    than raising `ZeroDivisionError`) when `total_capacity` is 0, e.g.
    because the tour has no concerts or only cancelled ones. Returns `None`
    when no tour with `tour_id` exists, so the router can translate that
    into a 404.
    """
    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        return None

    tickets_sold, total_capacity = (
        db.query(
            func.coalesce(func.sum(Concert.tickets_sold), 0),
            func.coalesce(func.sum(Venue.capacity), 0),
        )
        .join(Venue, Concert.venue_id == Venue.id)
        .filter(Concert.tour_id == tour_id, Concert.is_cancelled.is_(False))
        .first()
    )
    tickets_sold = int(tickets_sold)
    total_capacity = int(total_capacity)

    percentage_sold = (
        round(tickets_sold / total_capacity * 100, OCCUPANCY_PERCENTAGE_PRECISION)
        if total_capacity > 0
        else 0.0
    )

    return TourOccupancySchema(
        tour_id=tour_id,
        tickets_sold=tickets_sold,
        total_capacity=total_capacity,
        percentage_sold=percentage_sold,
    )


def duplicate_tour(db: Session, tour_id: int) -> Optional[Tour]:
    """Duplicate a tour as a new, persisted `planned` tour with no concerts.

    Copies `artist`, `start_date`, `end_date`, and `description` from the
    source tour, and names the copy `f"{source.name} (copy)"`. The source
    tour's concerts are not duplicated. Returns `None` when no tour with
    `tour_id` exists, so the router can translate that into a 404.
    """
    source = db.query(Tour).filter(Tour.id == tour_id).first()
    if source is None:
        return None

    duplicate = Tour(
        name=f"{source.name} (copy)",
        artist=source.artist,
        start_date=source.start_date,
        end_date=source.end_date,
        description=source.description,
        status=TourStatus.PLANNED.value,
    )
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    return duplicate


def cancel_tour(
    db: Session,
    tour_id: int,
    reason: str,
    reference_time: Optional[datetime] = None,
) -> int:
    """Cancel every upcoming, not-yet-cancelled concert on a tour.

    "Upcoming" means scheduled today or later, compared by calendar date
    against `reference_time` (defaulting to `get_reference_time()` when
    omitted), so a concert on the same calendar day counts as upcoming.
    Past concerts and concerts already marked cancelled are left
    untouched. Each newly cancelled concert gets `reason` stored on
    `cancellation_reason` and `cancelled_with_tour` set to `True`, so
    `uncancel_tour` can later tell them apart from independently
    cancelled concerts. Raises `TourNotFoundError` when no tour with
    `tour_id` exists. Commits once and returns the count of concerts
    newly cancelled by this call.
    """
    if reference_time is None:
        reference_time = get_reference_time()

    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        raise TourNotFoundError(f"Tour {tour_id} not found")

    concerts = (
        db.query(Concert)
        .filter(
            Concert.tour_id == tour_id,
            Concert.is_cancelled.is_(False),
            func.date(Concert.date_time) >= func.date(reference_time),
        )
        .all()
    )

    for concert in concerts:
        concert.is_cancelled = True
        concert.cancellation_reason = reason
        concert.cancelled_with_tour = True

    db.commit()
    return len(concerts)


def uncancel_tour(db: Session, tour_id: int) -> Tour:
    """Restore a cancelled tour to `planned`, along with any concerts that
    were cancelled alongside it.

    Raises `TourNotFoundError` when no tour with `tour_id` exists, and
    `TourConflictError` when the tour's status isn't `cancelled` (the
    message names its current status); in both cases no row is touched.
    On success, sets the tour's status to `planned`, restores every
    concert flagged `cancelled_with_tour` back to not-cancelled (also
    clearing its `cancellation_reason` and resetting the flag to `False`),
    leaves independently cancelled concerts (`cancelled_with_tour` is
    `False`) untouched, commits once, and returns the refreshed tour.
    """
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if tour is None:
        raise TourNotFoundError(f"Tour {tour_id} not found")
    if tour.status != CANCELLED_TOUR_STATUS:
        raise TourConflictError(
            f"Tour {tour_id} is not cancelled (status: {tour.status})"
        )

    tour.status = TourStatus.PLANNED.value

    concerts = (
        db.query(Concert)
        .filter(Concert.tour_id == tour_id, Concert.cancelled_with_tour.is_(True))
        .all()
    )
    for concert in concerts:
        concert.is_cancelled = False
        concert.cancellation_reason = None
        concert.cancelled_with_tour = False

    db.commit()
    db.refresh(tour)
    return tour


def get_sold_out_tours(db: Session) -> List[Tour]:
    """Return tours where every non-cancelled concert is sold out.

    A tour qualifies when it has at least one non-cancelled concert, and
    all of those non-cancelled concerts have sold out their venue's
    capacity (`tickets_sold >= capacity`). Tours with zero eligible
    concerts (none at all, or all cancelled) are excluded. Computed via a
    single grouped query comparing the count of non-cancelled concerts
    against the count of non-cancelled, sold-out ones per tour, rather
    than a Python loop.
    """
    is_sold_out = case(
        (and_(Venue.capacity.isnot(None), Concert.tickets_sold >= Venue.capacity), 1),
        else_=0,
    )

    qualifying_tour_ids = (
        db.query(Concert.tour_id)
        .join(Venue, Concert.venue_id == Venue.id)
        .filter(Concert.is_cancelled.is_(False))
        .group_by(Concert.tour_id)
        .having(func.count(Concert.id) == func.sum(is_sold_out))
        .scalar_subquery()
    )

    return db.query(Tour).filter(Tour.id.in_(qualifying_tour_ids)).all()


def _escape_like_wildcards(value: str) -> str:
    """Escape `\\`, `%`, and `_` so they're matched literally in a `LIKE`/
    `ILIKE` pattern instead of acting as wildcards."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_tours_by_artist(
    db: Session, artist: str, limit: int = MAX_ARTIST_SEARCH_RESULTS
) -> List[Tour]:
    """Return tours whose `artist` contains `artist`, case-insensitively.

    The match is a substring search (`%artist%`); `%` and `_` in `artist`
    are escaped so they're matched literally rather than acting as `LIKE`
    wildcards. Results are ordered by `artist`, then `id`, for a
    deterministic order, and capped at `limit`. Returns an empty list when
    `artist` is empty or matches nothing.
    """
    if not artist:
        return []

    pattern = f"%{_escape_like_wildcards(artist)}%"
    return (
        db.query(Tour)
        .filter(Tour.artist.ilike(pattern, escape="\\"))
        .order_by(Tour.artist, Tour.id)
        .limit(limit)
        .all()
    )
