"""Tour CRUD endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db, get_reference_time
from ..models import Concert, Tour, Venue
from ..schemas import ConcertResponse, TourCreate, TourUpdate, TourResponse, TourSummary

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
    db: Session = Depends(get_db)
):
    """Retrieve all tours with pagination."""
    tours = db.query(Tour).offset(skip).limit(limit).all()
    return tours


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
