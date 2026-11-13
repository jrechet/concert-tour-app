"""Tour dates endpoint: chronological ordering of concerts via the shared
`list_tour_dates` data-access helper."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..database import get_db, get_reference_time
from ..schemas.tour_date import TourDateResponse, TourDateSort
from ..services.tour_dates import list_tour_dates

router = APIRouter(prefix="/api/v1", tags=["tour-dates"])


@router.get("/tour-dates", response_model=List[TourDateResponse])
def get_tour_dates(
    include_past: bool = Query(
        True, description="When false, past concerts are excluded entirely"
    ),
    sort: TourDateSort = Query(
        TourDateSort.NEXT_FIRST,
        description="`next_first` (default): upcoming ascending then past descending. `date_desc`: strictly descending by date.",
    ),
    limit: int = Query(
        DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description=f"Maximum number of tour dates to return, up to {MAX_PAGE_SIZE}"
    ),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve tour dates in chronological order.

    By default (`sort=next_first`), ordering is delegated entirely to
    `list_tour_dates`: upcoming concerts (ascending, soonest first)
    followed by past ones (descending, most recent first), so the first
    element is always the next concert. `include_past=false` excludes past
    concerts rather than appending them. `sort=date_desc` instead returns
    every included concert in strictly descending date order.
    """
    tour_dates = list_tour_dates(db, include_past=include_past, reference_time=reference_time)

    if sort == TourDateSort.DATE_DESC:
        tour_dates = sorted(tour_dates, key=lambda concert: concert.date_time, reverse=True)

    return tour_dates[:limit]
