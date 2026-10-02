"""Query logic backing the concerts CSV export and upcoming-concerts endpoints."""

import csv
import io
from datetime import date, datetime, timezone
from typing import Iterator, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Query, Session, joinedload

from ..database import get_reference_time
from ..models import Concert, Venue
from ..schemas.concert import ConcertPriceFilter
from ..schemas.occupancy import OccupancyResponse

CSV_HEADER = ["date", "city", "venue", "tour"]


class ConcertNotFoundError(Exception):
    """Raised by `sell_tickets` when no concert with the given id exists."""


class ConcertCancelledError(Exception):
    """Raised by `sell_tickets` when the target concert has been cancelled."""


class ConcertCapacityExceededError(Exception):
    """Raised by `sell_tickets` when the sale would exceed the venue's capacity."""


class InsufficientSoldTicketsError(Exception):
    """Raised by `refund_tickets` when the requested quantity exceeds the
    concert's current `tickets_sold` count."""


class InvalidDateError(Exception):
    """Raised by `reschedule_concert` when the requested `new_date_time`
    is not in the future."""


def apply_price_filter(query: Query, price_filter: ConcertPriceFilter) -> Query:
    """Apply the validated `min_price`/`max_price` filter to a concerts query.

    `price_filter` has already been validated at the API layer (non-negative,
    and `min_price` <= `max_price` when both are given). Both bounds are
    inclusive. When either bound is given, concerts with no `ticket_price`
    set are excluded entirely, since a null price can't be compared against
    a threshold; when neither is given, the query is left untouched and such
    concerts are still included.
    """
    if price_filter.min_price is None and price_filter.max_price is None:
        return query

    query = query.filter(Concert.ticket_price.isnot(None))
    if price_filter.min_price is not None:
        query = query.filter(Concert.ticket_price >= price_filter.min_price)
    if price_filter.max_price is not None:
        query = query.filter(Concert.ticket_price <= price_filter.max_price)
    return query


def is_past(concert: Concert, reference_time: Optional[datetime] = None) -> bool:
    """Whether `concert`'s calendar date is strictly before `reference_time`'s.

    Compares calendar dates only (not exact timestamps), so a concert later
    today is not past. `reference_time` defaults to `get_reference_time()`
    when omitted. Operates on an already-loaded `Concert`, so it's directly
    testable with a plain object/mock rather than a DB-backed one, and is
    the single source of truth for "is this concert past" so that rule
    isn't reimplemented ad hoc at each call site.
    """
    if reference_time is None:
        reference_time = get_reference_time()
    return concert.date_time.date() < reference_time.date()


def get_upcoming_concerts(
    db: Session,
    reference_time: Optional[datetime] = None,
    show_past: bool = False,
) -> List[Concert]:
    """Return concerts ordered soonest first, by date ascending.

    When `show_past` is False (default), only concerts scheduled today or
    later are returned, compared against `reference_time` (defaulting to
    `get_reference_time()`, i.e. the app's current date, when omitted);
    past concerts are excluded entirely. When `show_past` is True, every
    concert is returned instead, past and future alike, still ordered
    chronologically. The date boundary mirrors `is_past`'s semantics
    (calendar date, not exact timestamp).
    """
    if reference_time is None:
        reference_time = get_reference_time()
    query = db.query(Concert).options(joinedload(Concert.venue))
    if not show_past:
        query = query.filter(func.date(Concert.date_time) >= func.date(reference_time))
    return query.order_by(Concert.date_time).all()


def get_concerts_between_dates(db: Session, start: date, end: date) -> List[Concert]:
    """Return concerts whose calendar date falls within `start`/`end`, inclusive.

    Both bounds are inclusive and compared against `Concert.date_time`'s
    calendar date (not exact timestamp), mirroring `is_past`/`get_upcoming_concerts`.
    Ordered soonest first, by date ascending. Returns an empty list when no
    concert falls in range.
    """
    return (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(func.date(Concert.date_time) >= start)
        .filter(func.date(Concert.date_time) <= end)
        .order_by(Concert.date_time)
        .all()
    )


def get_next_concert(db: Session, reference_time: Optional[datetime] = None) -> Optional[Concert]:
    """Return the soonest upcoming, non-cancelled concert, or `None`.

    A concert is eligible when its exact `date_time` is at or after
    `reference_time` (defaulting to `get_reference_time()` when omitted)
    and it has not been cancelled. Eager-loads `Concert.venue` via
    `joinedload` to avoid N+1 queries.
    """
    if reference_time is None:
        reference_time = get_reference_time()
    return (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(Concert.date_time >= reference_time)
        .filter(Concert.is_cancelled.is_(False))
        .order_by(Concert.date_time)
        .first()
    )


def get_sold_out_concerts(db: Session, reference_time: Optional[datetime] = None) -> List[Concert]:
    """Return upcoming, non-cancelled concerts with zero tickets remaining.

    A concert is eligible when its exact `date_time` is at or after
    `reference_time` (defaulting to `get_reference_time()` when omitted,
    mirroring `get_next_concert`), it has not been cancelled, and its
    venue's capacity has been fully sold (`tickets_sold >= capacity`,
    via the real `Concert.venue` relationship rather than a hardcoded
    number). Concerts whose venue has no known capacity can't be sold
    out and are excluded. Ordered soonest first, by date ascending.
    Eager-loads `Concert.venue` via `joinedload` to avoid N+1 queries.
    """
    if reference_time is None:
        reference_time = get_reference_time()
    return (
        db.query(Concert)
        .join(Venue, Concert.venue_id == Venue.id)
        .options(joinedload(Concert.venue))
        .filter(Concert.date_time >= reference_time)
        .filter(Concert.is_cancelled.is_(False))
        .filter(Venue.capacity.isnot(None))
        .filter(Concert.tickets_sold >= Venue.capacity)
        .order_by(Concert.date_time)
        .all()
    )


def get_concerts_for_export(db: Session) -> List[dict]:
    """Fetch every concert joined with its venue and tour, ordered by date.

    Returns plain dicts (`date`, `city`, `venue`, `tour`) decoupled from the
    HTTP layer, so this can be unit tested without going through the export
    endpoint. Eager-loads `Concert.venue`/`Concert.tour` via `joinedload` to
    avoid N+1 queries. Returns an empty list when there are no concerts.
    """
    concerts = (
        db.query(Concert)
        .options(joinedload(Concert.venue), joinedload(Concert.tour))
        .order_by(Concert.date_time)
        .all()
    )
    return [
        {
            "date": concert.date_time.date().isoformat(),
            "city": concert.venue.city,
            "venue": concert.venue.name,
            "tour": concert.tour.name,
        }
        for concert in concerts
    ]


def get_concert_occupancy(db: Session, concert_id: int) -> Optional[OccupancyResponse]:
    """Compute ticket sales relative to venue capacity for a single concert.

    Returns `None` when no concert with `concert_id` exists, so the router
    can translate that into a 404. `capacity` and `percentage_sold` are
    both null when the concert's venue has no capacity set; otherwise
    `percentage_sold` is `tickets_sold / capacity * 100`, rounded to 1
    decimal place.
    """
    row = (
        db.query(Concert.tickets_sold, Venue.capacity)
        .join(Venue, Concert.venue_id == Venue.id)
        .filter(Concert.id == concert_id)
        .first()
    )
    if row is None:
        return None

    tickets_sold, capacity = row
    percentage_sold = round(tickets_sold / capacity * 100, 1) if capacity else None

    return OccupancyResponse(
        concert_id=concert_id,
        tickets_sold=tickets_sold,
        capacity=capacity,
        percentage_sold=percentage_sold,
    )


def sell_tickets(concert_id: int, quantity: int, db: Session) -> Concert:
    """Sell `quantity` tickets for the concert identified by `concert_id`.

    Raises `ConcertNotFoundError` when no such concert exists,
    `ConcertCancelledError` when the concert has been cancelled, and
    `ConcertCapacityExceededError` when `tickets_sold + quantity` would
    exceed the linked venue's capacity (via the real `Concert.venue`
    relationship, not a hardcoded id). Capacity is treated as unlimited
    when the venue has none set. On success, increments `tickets_sold`,
    commits, and returns the updated concert.
    """
    concert = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(Concert.id == concert_id)
        .first()
    )
    if concert is None:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")
    if concert.is_cancelled:
        raise ConcertCancelledError(f"Concert {concert_id} is cancelled")

    capacity = concert.venue.capacity
    if capacity is not None and concert.tickets_sold + quantity > capacity:
        raise ConcertCapacityExceededError(
            f"Concert {concert_id} cannot sell {quantity} tickets: only "
            f"{capacity - concert.tickets_sold} remaining of {capacity} capacity"
        )

    concert.tickets_sold += quantity
    db.commit()
    db.refresh(concert)
    return concert


def refund_tickets(concert_id: int, quantity: int, db: Session) -> Concert:
    """Refund `quantity` previously sold tickets for the concert identified
    by `concert_id`.

    Raises `ConcertNotFoundError` when no such concert exists, and
    `InsufficientSoldTicketsError` when `quantity` exceeds the concert's
    current `tickets_sold` count, so a refund can never drive it negative.
    On success, decrements `tickets_sold`, commits, and returns the updated
    concert.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if concert is None:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")

    if quantity > concert.tickets_sold:
        raise InsufficientSoldTicketsError(
            f"Concert {concert_id} cannot refund {quantity} tickets: only "
            f"{concert.tickets_sold} currently sold"
        )

    concert.tickets_sold -= quantity
    db.commit()
    db.refresh(concert)
    return concert


def reschedule_concert(db: Session, concert_id: int, new_date_time: datetime) -> Concert:
    """Move the concert identified by `concert_id` to `new_date_time`.

    Raises `ConcertNotFoundError` when no such concert exists,
    `ConcertCancelledError` when the concert has been cancelled, and
    `InvalidDateError` when `new_date_time` is not in the future. The
    future check compares in UTC, treating a naive `new_date_time` as
    already being UTC (mirroring `calendar_service.DEFAULT_TIMEZONE`),
    so naive and timezone-aware inputs are handled consistently. On
    success, updates `date_time`, commits, and returns the updated concert.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if concert is None:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")
    if concert.is_cancelled:
        raise ConcertCancelledError(f"Concert {concert_id} is cancelled")

    aware_new_date_time = (
        new_date_time if new_date_time.tzinfo is not None else new_date_time.replace(tzinfo=timezone.utc)
    )
    if aware_new_date_time < datetime.now(timezone.utc):
        raise InvalidDateError(f"new_date_time {new_date_time} must be in the future")

    concert.date_time = new_date_time
    db.commit()
    db.refresh(concert)
    return concert


def generate_concerts_csv(db: Session) -> Iterator[str]:
    """Yield the concerts CSV export, one row per concert, ordered by date.

    The first yielded chunk is always the header row (`date,city,venue,tour`),
    even when there are no concerts. Values are written through Python's
    `csv` module so commas/quotes in city, venue, or tour names are escaped
    correctly.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(CSV_HEADER)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in get_concerts_for_export(db):
        writer.writerow([row["date"], row["city"], row["venue"], row["tour"]])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
