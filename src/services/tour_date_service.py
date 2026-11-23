"""Chronological ordering of tour dates for the data/service layer.

A "tour date" is represented by the `Concert` model in this codebase (a
concert on a tour, at a venue, on a given `date_time`). `list_tour_dates`
is the single source of truth for "next concert first" ordering, so
callers never need to re-sort results in Python.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import case
from sqlalchemy.orm import Session

from ..database import get_reference_time
from ..models import Concert, Venue


def list_tour_dates(
    db: Session,
    *,
    reference_time: Optional[datetime] = None,
) -> List[Concert]:
    """Return tour dates ordered "next concert first".

    Upcoming dates (`date_time >= reference_time`) are returned first,
    ascending, so index 0 is always the next concert. Past dates follow,
    also ascending (oldest of the past dates first).

    `reference_time` defaults to `get_reference_time()` when omitted, so
    tests never depend on the real wall clock. A concert scheduled exactly
    at `reference_time` counts as upcoming.

    All ordering is expressed as a SQL `ORDER BY` (not done in Python
    after fetching). Ties on the same `date_time` are broken by the
    venue's name, then by `id`, for a deterministic result.
    """
    if reference_time is None:
        reference_time = get_reference_time()

    is_upcoming = Concert.date_time >= reference_time

    return (
        db.query(Concert)
        .join(Venue, Concert.venue_id == Venue.id)
        .order_by(
            case((is_upcoming, 0), else_=1),
            Concert.date_time.asc(),
            Venue.name.asc(),
            Concert.id.asc(),
        )
        .all()
    )
