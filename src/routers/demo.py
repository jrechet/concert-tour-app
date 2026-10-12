"""Read-only aggregated view of the seeded demo tour.

`GET /api/v1/demo/tour-overview` answers "what does my tour look like" in
one call: the tour's name/artist/status, every concert with its venue,
city, date and priced ticket tiers, and aggregate past/upcoming counts.
It is gated by `config.DEMO_ENABLED` (off by default) and only ever reads
the rows `src.demo.seeder.seed_demo` would have written — it never
seeds data itself.

`GET /demo` and `GET /demo/concerts` (below, on `page_router`) render that
same overview as an HTML walkthrough instead of JSON: both read through
`_build_tour_overview`, the helper the JSON endpoint also calls, so the
page and the API can never drift apart on what "the tour" contains.
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import config
from ..database import get_db, get_reference_time
from ..demo.config import DEMO_TOUR_NAME
from ..models import Concert, TicketTier, Tour, Venue
from ..schemas.demo import DemoConcertOut, DemoTicketTierOut, DemoTourOverviewResponse

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])
page_router = APIRouter(tags=["demo-page"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _require_demo_enabled() -> None:
    """Raise 403 unless the demo feature flag is on."""
    if not config.DEMO_ENABLED:
        raise HTTPException(status_code=403, detail="Demo mode is disabled")


def _get_demo_tour(db: Session) -> Tour:
    """Fetch the seeded demo tour, or raise 404 if it hasn't been seeded."""
    tour = db.query(Tour).filter(Tour.name == DEMO_TOUR_NAME).one_or_none()
    if tour is None:
        raise HTTPException(status_code=404, detail="Demo tour has not been seeded")
    return tour


def _build_tour_overview(
    db: Session, tour: Tour, reference_time: datetime, city: Optional[str] = None
) -> DemoTourOverviewResponse:
    """Assemble the aggregated tour-overview response for an already-fetched
    `tour`, optionally narrowed to one (already-normalized) `city`."""
    concerts_query = (
        db.query(Concert)
        .join(Venue, Concert.venue_id == Venue.id)
        .options(joinedload(Concert.venue))
        .filter(Concert.tour_id == tour.id)
    )
    if city is not None:
        concerts_query = concerts_query.filter(func.lower(Venue.city) == city.lower())
    concerts = concerts_query.order_by(Concert.date_time, Concert.id).all()

    tiers_by_concert_id = defaultdict(list)
    concert_ids = [concert.id for concert in concerts]
    if concert_ids:
        tiers = (
            db.query(TicketTier)
            .filter(TicketTier.concert_id.in_(concert_ids))
            .order_by(TicketTier.id)
            .all()
        )
        for tier in tiers:
            tiers_by_concert_id[tier.concert_id].append(tier)

    reference_date = reference_time.date()
    concert_items = []
    past_count = 0
    upcoming_count = 0
    for concert in concerts:
        is_past = concert.date_time.date() < reference_date
        past_count += is_past
        upcoming_count += not is_past
        concert_items.append(
            DemoConcertOut(
                id=concert.id,
                venue_name=concert.venue_name,
                city=concert.venue_city,
                date_time=concert.date_time,
                status="past" if is_past else "upcoming",
                ticket_tiers=[
                    DemoTicketTierOut(name=tier.name, price=tier.price)
                    for tier in tiers_by_concert_id.get(concert.id, [])
                ],
            )
        )

    return DemoTourOverviewResponse(
        tour_name=tour.name,
        artist=tour.artist,
        status=tour.status,
        concert_count=len(concert_items),
        past_concert_count=past_count,
        upcoming_concert_count=upcoming_count,
        concerts=concert_items,
    )


@router.get("/tour-overview", response_model=DemoTourOverviewResponse)
def get_demo_tour_overview(
    city: Optional[str] = Query(
        None, min_length=1, description="Filter concerts by city, case-insensitively"
    ),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve the seeded demo tour, optionally filtered to one city.

    Returns 403 if the demo feature is disabled, 404 if no demo tour has
    been seeded yet. An unrecognized `city` yields 200 with an empty
    `concerts` list rather than a 404, since the tour itself still exists;
    a blank/whitespace-only `city` is rejected with 422.
    """
    _require_demo_enabled()
    tour = _get_demo_tour(db)

    normalized_city = None
    if city is not None:
        normalized_city = city.strip()
        if not normalized_city:
            raise HTTPException(status_code=422, detail="city must not be blank")

    return _build_tour_overview(db, tour, reference_time, normalized_city)


@page_router.get("/demo", response_class=HTMLResponse)
def get_demo_walkthrough(
    request: Request,
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Render the band-facing demo as a step-by-step walkthrough: create
    band, add venues, schedule concerts, track upcoming dates, ticket
    tiers. Read-only — it renders the same overview `tour-overview` builds
    and never writes to the database. 403 if the demo feature is disabled,
    404 if no demo tour has been seeded yet.
    """
    _require_demo_enabled()
    tour = _get_demo_tour(db)
    overview = _build_tour_overview(db, tour, reference_time)
    cities = sorted({concert.city for concert in overview.concerts})
    return templates.TemplateResponse(
        request, "demo/walkthrough.html", {"overview": overview, "cities": cities}
    )


@page_router.get("/demo/concerts", response_class=HTMLResponse)
def get_demo_concert_fragment(
    request: Request,
    city: Optional[str] = Query(None, description="Filter the concert list by city, case-insensitively"),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """HTMX fragment backing the walkthrough page's city filter: the same
    concert list markup, narrowed to `city` (or the full list when `city`
    is blank/omitted). Returns only the fragment, not a full HTML document.
    """
    _require_demo_enabled()
    tour = _get_demo_tour(db)
    normalized_city = city.strip() if city and city.strip() else None
    overview = _build_tour_overview(db, tour, reference_time, normalized_city)
    return templates.TemplateResponse(
        request, "demo/_concert_list.html", {"concerts": overview.concerts}
    )
