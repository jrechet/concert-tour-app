"""Query logic backing tour-level aggregates, such as ticket revenue."""

from datetime import date
from decimal import Decimal
from typing import List, NamedTuple, Optional

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from ..models import Concert, Tour, Venue
from ..schemas.tour import TourStatus


class TourRevenue(NamedTuple):
    """Ticket revenue for a tour, and the count of concerts it was summed over."""

    revenue: Decimal
    concert_count: int


class TourNotFoundError(Exception):
    """Raised by `get_tour_span` when no tour with the given id exists."""


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


def get_tour_cities(db: Session, tour_id: int) -> Optional[List[str]]:
    """Return the distinct cities a tour passes through, in date order.

    Cancelled concerts are excluded. When a city is visited more than once,
    only its first occurrence (by concert date) determines its position.
    Returns `None` when no tour with `tour_id` exists, so the router can
    translate that into a 404.
    """
    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        return None

    cities = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Concert.tour_id == tour_id, Concert.is_cancelled.is_(False))
        .order_by(Concert.date_time)
        .all()
    )

    seen = set()
    distinct_cities = []
    for (city,) in cities:
        if city not in seen:
            seen.add(city)
            distinct_cities.append(city)
    return distinct_cities


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


def search_by_artist(db: Session, artist: str) -> List[Tour]:
    """Return all tours whose `artist` contains `artist`, case-insensitively.

    Returns an empty list when `artist` is empty or matches nothing.
    """
    if not artist:
        return []

    return (
        db.query(Tour)
        .filter(func.lower(Tour.artist).contains(artist.lower()))
        .all()
    )
