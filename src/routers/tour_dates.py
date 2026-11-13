"""Tour dates endpoint: chronological ordering of concerts via the shared
`list_tour_dates` data-access helper."""

from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..database import get_db, get_reference_time
from ..schemas.tour_date import TourDateResponse, TourDateSort
from ..services.tour_dates import list_tour_dates

router = APIRouter(prefix="/api/v1", tags=["tour-dates"])
page_router = APIRouter(tags=["tour-dates-page"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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


@page_router.get("/tour-dates", response_class=HTMLResponse)
def get_tour_dates_page(
    request: Request,
    include_past: bool = Query(
        False, description="When true, past concerts are shown in a separate section below the upcoming ones"
    ),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Render the tour dates list, next concert first.

    Consumes `list_tour_dates` directly, so the DOM order always matches
    the API order (no sorting happens in the template). A plain request
    renders the full page; a request carrying the `HX-Request` header —
    sent by the "Show past dates" toggle — renders only the list
    partial, so the same markup backs both the initial page load and
    every subsequent HTMX swap.
    """
    tour_dates = list_tour_dates(db, include_past=include_past, reference_time=reference_time)

    context = {
        "tour_dates": tour_dates,
        "reference_time": reference_time,
        "include_past": include_past,
    }

    template_name = (
        "partials/tour_date_list.html"
        if request.headers.get("HX-Request") == "true"
        else "tour_dates.html"
    )
    return templates.TemplateResponse(request, template_name, context)
