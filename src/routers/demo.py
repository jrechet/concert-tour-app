"""Read-only aggregated view of the seeded demo tour.

`GET /api/v1/demo/tour-overview` answers "what does my tour look like" in
one call: the tour's name/artist/status, every concert with its venue,
city, date and priced ticket tiers, and aggregate past/upcoming counts.
It is gated by `config.DEMO_ENABLED` (off by default) and only ever reads
the rows `src.demo.seeder.seed_demo` would have written — it never
seeds data itself.
"""

from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import config
from ..database import get_db, get_reference_time
from ..demo.config import DEMO_TOUR_NAME
from ..models import Concert, TicketTier, Tour, Venue
from ..schemas.demo import DemoConcertOut, DemoTicketTierOut, DemoTourOverviewResponse

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


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
    if not config.DEMO_ENABLED:
        raise HTTPException(status_code=403, detail="Demo mode is disabled")

    tour = db.query(Tour).filter(Tour.name == DEMO_TOUR_NAME).one_or_none()
    if tour is None:
        raise HTTPException(status_code=404, detail="Demo tour has not been seeded")

    normalized_city = None
    if city is not None:
        normalized_city = city.strip()
        if not normalized_city:
            raise HTTPException(status_code=422, detail="city must not be blank")

    concerts_query = (
        db.query(Concert)
        .join(Venue, Concert.venue_id == Venue.id)
        .options(joinedload(Concert.venue))
        .filter(Concert.tour_id == tour.id)
    )
    if normalized_city is not None:
        concerts_query = concerts_query.filter(func.lower(Venue.city) == normalized_city.lower())
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
