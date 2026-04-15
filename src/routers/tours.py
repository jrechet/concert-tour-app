"""Tour CRUD endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Tour
from ..schemas import TourCreate, TourUpdate, TourResponse

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
