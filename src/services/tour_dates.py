"""Chronological ordering of tour dates, shared by the API and the UI.

A "tour date" is represented by the `Concert` model in this codebase (a
concert on a tour, at a venue, on a given `date_time`). `list_tour_dates`
is the single source of truth for "next concert first" ordering, so the
API and the UI never reimplement this rule separately.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import case
from sqlalchemy.orm import Query, Session

from ..database import get_reference_time
from ..models import Concert


def list_tour_dates(
    db: Session,
    *,
    include_past: bool = True,
    reference_time: Optional[datetime] = None,
) -> List[Concert]:
    """Return tour dates ordered "next concert first".

    Upcoming dates (`date_time >= reference_time`) are returned first,
    ascending, so index 0 is always the next concert. Past dates follow,
    most recent first (descending). When `include_past` is False, past
    dates are excluded entirely instead.

    `reference_time` defaults to `get_reference_time()` when omitted, so
    tests never depend on the real wall clock. A concert scheduled exactly
    at `reference_time` counts as upcoming.

    All ordering is expressed as a SQL `ORDER BY` (not done in Python
    after fetching), so it can be reused by paginated queries. Ties on the
    same `date_time` are broken by ascending `id`, for a deterministic
    result.
    """
    if reference_time is None:
        reference_time = get_reference_time()

    is_upcoming = Concert.date_time >= reference_time

    query: Query = db.query(Concert)
    if not include_past:
        query = query.filter(is_upcoming)

    return query.order_by(
        case((is_upcoming, 0), else_=1),
        case((is_upcoming, Concert.date_time), else_=None).asc(),
        case((is_upcoming, None), else_=Concert.date_time).desc(),
        Concert.id.asc(),
    ).all()
