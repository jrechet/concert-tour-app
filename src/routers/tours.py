"""Tour CRUD endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload, selectinload

from ..database import get_db, get_reference_time
from ..models import Concert, Tour, Venue
from ..schemas import (
    CancelTourRequest,
    CancelTourResponse,
    ConcertResponse,
    TourCitiesResponse,
    TourCreate,
    TourUpdate,
    TourOccupancyResponse,
    TourResponse,
    TourSpanResponse,
    TourStatus,
    TourSummary,
    TourRevenue,
)
from ..services.calendar_service import build_tour_calendar
from ..services.occupancy import TourNotFoundError as OccupancyTourNotFoundError, get_tour_occupancy
from ..services.tour_service import (
    TourNotFoundError,
    get_tour_cities,
    get_tour_revenue,
    get_tour_span,
    search_by_artist,
)

router = APIRouter(prefix="/api/v1/tours", tags=["tours"])


@router.post("/", response_model=TourResponse, status_code=201)
def create_tour(tour: TourCreate, db: Session = Depends(get_db)):
    """Create a new tour."""
    db_tour = Tour(
        name=tour.name,
        artist=tour.artist,
        description=tour.description,
        start_date=tour.start_date,
        end_date=tour.end_date,
        status=tour.status
    )
    db.add(db_tour)
    db.commit()
    db.refresh(db_tour)
    return db_tour


@router.get("/", response_model=List[TourResponse])
def get_tours(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TourStatus] = Query(None, description="Filter tours by status"),
    db: Session = Depends(get_db)
):
    """Retrieve all tours with pagination, optionally filtered by status."""
    query = db.query(Tour)
    if status is not None:
        query = query.filter(Tour.status == status.value)
    tours = query.offset(skip).limit(limit).all()
    return tours


@router.get("/search", response_model=List[TourResponse])
def search_tours_by_artist(artist: str = Query(...), db: Session = Depends(get_db)):
    """Search tours whose artist contains the given text, case-insensitively."""
    return search_by_artist(db, artist)


@router.get("/{tour_id}", response_model=TourResponse)
def get_tour(tour_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific tour by ID."""
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour


@router.get("/{tour_id}/dates", response_model=List[ConcertResponse])
def get_tour_dates(
    tour_id: int,
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve a tour's concerts in chronological order.

    Upcoming concerts (today or later, compared by calendar date against
    `reference_time`) come first, soonest first. Past concerts are appended
    afterward, oldest first, so the full list stays chronological end to
    end. Returns 404 if the tour doesn't exist, or an empty list if it has
    no concerts.
    """
    tour_exists = db.query(Tour.id).filter(Tour.id == tour_id).first()
    if not tour_exists:
        raise HTTPException(status_code=404, detail="Tour not found")

    is_past = case(
        (func.date(Concert.date_time) < func.date(reference_time), 1),
        else_=0,
    )
    concerts = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(Concert.tour_id == tour_id)
        # Concert.id is a tiebreaker so concerts sharing the same date_time
        # still come back in a stable, deterministic order.
        .order_by(is_past, Concert.date_time, Concert.id)
        .all()
    )
    return concerts


@router.get("/{tour_id}/summary", response_model=TourSummary)
def get_tour_summary(tour_id: int, db: Session = Depends(get_db)):
    """Retrieve aggregate stats for a tour's dates.

    Returns 404 if the tour doesn't exist. A tour with no concerts yields
    a zeroed-out summary with null first/last dates.
    """
    tour_exists = db.query(Tour.id).filter(Tour.id == tour_id).first()
    if not tour_exists:
        raise HTTPException(status_code=404, detail="Tour not found")

    date_count, first_date, last_date = (
        db.query(
            func.count(Concert.id),
            func.min(Concert.date_time),
            func.max(Concert.date_time),
        )
        .filter(Concert.tour_id == tour_id)
        .one()
    )
    distinct_city_count = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Concert.tour_id == tour_id)
        .distinct()
        .count()
    )

    return TourSummary(
        tour_id=tour_id,
        date_count=date_count,
        first_date=first_date.date() if first_date else None,
        last_date=last_date.date() if last_date else None,
        distinct_city_count=distinct_city_count,
    )


@router.get("/{tour_id}/span", response_model=TourSpanResponse)
def get_tour_span_endpoint(tour_id: int, db: Session = Depends(get_db)):
    """Retrieve a tour's date span, derived from its non-cancelled concerts.

    Returns 404 if the tour doesn't exist. A tour with zero non-cancelled
    concerts yields a response with all-null fields.
    """
    try:
        span = get_tour_span(tour_id, db)
    except TourNotFoundError:
        raise HTTPException(status_code=404, detail="Tour not found")
    return TourSpanResponse(
        first_date=span.first_date,
        last_date=span.last_date,
        days_between=span.days_between,
    )


@router.get("/{tour_id}/cities", response_model=TourCitiesResponse)
def get_tour_cities_endpoint(tour_id: int, db: Session = Depends(get_db)):
    """Retrieve the distinct cities a tour passes through, in date order.

    Returns 404 if the tour doesn't exist.
    """
    cities = get_tour_cities(db, tour_id)
    if cities is None:
        raise HTTPException(status_code=404, detail="Tour not found")
    return TourCitiesResponse(tour_id=tour_id, cities=cities)


@router.get("/{tour_id}/calendar.ics")
def get_tour_calendar(tour_id: int, db: Session = Depends(get_db)):
    """Retrieve a tour's concerts as a downloadable iCalendar (.ics) feed.

    Returns 404 if the tour doesn't exist. A tour with no concerts yields a
    valid calendar with zero events.
    """
    tour = (
        db.query(Tour)
        .options(selectinload(Tour.concerts).joinedload(Concert.venue))
        .filter(Tour.id == tour_id)
        .first()
    )
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    ics_bytes = build_tour_calendar(tour)
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="tour-{tour_id}.ics"'},
    )


@router.get("/{tour_id}/revenue", response_model=TourRevenue)
def get_tour_revenue_endpoint(tour_id: int, db: Session = Depends(get_db)):
    """Retrieve total ticket revenue for a tour and the concert count it covers.

    Returns 404 if the tour doesn't exist.
    """
    result = get_tour_revenue(db, tour_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Tour not found")
    return result


@router.get("/{tour_id}/occupancy", response_model=TourOccupancyResponse)
def get_tour_occupancy_endpoint(tour_id: int, db: Session = Depends(get_db)):
    """Retrieve ticket occupancy for a tour, aggregated over its non-cancelled concerts.

    Returns 404 if the tour doesn't exist.
    """
    try:
        result = get_tour_occupancy(db, tour_id)
    except OccupancyTourNotFoundError:
        raise HTTPException(status_code=404, detail="Tour not found")
    return TourOccupancyResponse(
        tickets_sold=result.tickets_sold,
        total_capacity=result.total_capacity,
        percentage_sold=result.percentage_sold,
    )


@router.post("/{tour_id}/cancel", response_model=CancelTourResponse)
def cancel_tour(
    tour_id: int,
    payload: CancelTourRequest,
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Cancel every upcoming, not-yet-cancelled concert on a tour.

    Returns 404 if the tour doesn't exist. Past concerts and concerts
    already marked cancelled are left untouched. A concert scheduled on
    the same calendar day as `reference_time` is treated as upcoming
    (the same-day boundary is inclusive). Returns the count of
    concerts newly cancelled by this call.
    """
    tour_exists = db.query(Tour.id).filter(Tour.id == tour_id).first()
    if not tour_exists:
        raise HTTPException(status_code=404, detail="Tour not found")

    concerts = (
        db.query(Concert)
        .filter(
            Concert.tour_id == tour_id,
            Concert.is_cancelled.is_(False),
            func.date(Concert.date_time) >= func.date(reference_time),
        )
        .all()
    )

    for concert in concerts:
        concert.is_cancelled = True
        concert.cancellation_reason = payload.reason

    db.commit()
    return CancelTourResponse(cancelled_count=len(concerts))


@router.put("/{tour_id}", response_model=TourResponse)
def update_tour(tour_id: int, tour_update: TourUpdate, db: Session = Depends(get_db)):
    """Update an existing tour."""
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    # Update fields that are provided
    update_data = tour_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tour, field, value)
    
    db.commit()
    db.refresh(tour)
    return tour


@router.delete("/{tour_id}", status_code=204)
def delete_tour(tour_id: int, db: Session = Depends(get_db)):
    """Delete a tour."""
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    db.delete(tour)
    db.commit()
