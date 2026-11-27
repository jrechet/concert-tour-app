"""Data-layer pagination for the concert list endpoint."""

from typing import List, Tuple

from sqlalchemy.orm import Session

from ..models import Concert


def list_paginated(db: Session, offset: int, limit: int) -> Tuple[List[Concert], int]:
    """Return a page of every concert plus the unfiltered total count.

    Ordered by `date_time` ascending with `id` as a stable tiebreak, so
    consecutive pages neither overlap nor skip rows. The total is computed
    with a `SELECT COUNT(*)` against the same base query (not `len()` of
    the page), so it reflects every row regardless of `offset`/`limit`.
    An `offset` past the end of the table returns an empty list alongside
    the real total, rather than raising.
    """
    base_query = db.query(Concert)
    total = base_query.count()
    concerts = (
        base_query.order_by(Concert.date_time.asc(), Concert.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return concerts, total
