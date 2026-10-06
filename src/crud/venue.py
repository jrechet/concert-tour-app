"""Query logic backing the venue-detail endpoint."""

from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, contains_eager

from ..database import get_reference_time
from ..models import Concert, Venue


def get_venue_with_upcoming_concerts(db: Session, venue_id: int) -> Optional[Venue]:
    """Return the venue with id `venue_id`, its `concerts` relationship
    populated with only the upcoming, non-cancelled ones.

    A concert is "upcoming" when its `date_time` is at or after
    `get_reference_time()`, mirroring `get_next_concert`'s definition.
    The eligible concerts are ordered soonest first (ascending by date).
    Uses an outer join plus `contains_eager` so the real `Concert.venue`
    foreign key relationship drives the filtering/loading in a single
    query, and a venue with no eligible concerts still comes back (with an
    empty `concerts` list) rather than being dropped by the join. Returns
    `None` when no venue with `venue_id` exists, so the router can
    translate that into a 404.
    """
    reference_time = get_reference_time()
    # `.first()` would add a SQL `LIMIT 1` to a query that joins one venue
    # row to many concert rows, truncating the eager-loaded collection to a
    # single concert; `.all()` lets every joined row contribute to it, and
    # the ORM's identity map collapses them back into one `Venue` object.
    results = (
        db.query(Venue)
        .outerjoin(
            Concert,
            and_(
                Concert.venue_id == Venue.id,
                Concert.date_time >= reference_time,
                Concert.is_cancelled.is_(False),
            ),
        )
        .options(contains_eager(Venue.concerts))
        .filter(Venue.id == venue_id)
        .order_by(Concert.date_time)
        .all()
    )
    return results[0] if results else None
