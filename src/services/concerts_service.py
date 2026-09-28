"""Query logic backing the concerts CSV export and upcoming-concerts endpoints."""

import csv
import io
from datetime import datetime
from typing import Iterator, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Query, Session, joinedload

from ..database import get_reference_time
from ..models import Concert, Venue
from ..schemas.concert import ConcertPriceFilter
from ..schemas.occupancy import OccupancyResponse

CSV_HEADER = ["date", "city", "venue", "tour"]


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


def get_upcoming_concerts(db: Session, reference_time: Optional[datetime] = None) -> List[Concert]:
    """Return concerts scheduled today or later, ordered soonest first.

    A concert is upcoming when its calendar date is today or in the
    future, compared against `reference_time` (defaulting to
    `get_reference_time()`, i.e. the app's current date, when omitted).
    Past concerts are excluded entirely.
    """
    if reference_time is None:
        reference_time = get_reference_time()
    return (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(func.date(Concert.date_time) >= func.date(reference_time))
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
