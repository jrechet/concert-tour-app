from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Tour
from schemas import TourCreate, TourResponse

router = APIRouter(prefix="/api/v1/tours", tags=["tours"])


@router.get("", response_model=List[TourResponse])
async def get_tours(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Get tours with pagination."""
    try:
        tours = db.query(Tour).offset(offset).limit(limit).all()
        return tours
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=TourResponse, status_code=201)
async def create_tour(tour: TourCreate, db: Session = Depends(get_db)):
    """Create a new tour."""
    try:
        db_tour = Tour(**tour.dict())
        db.add(db_tour)
        db.commit()
        db.refresh(db_tour)
        return db_tour
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create tour")


@router.get("/{tour_id}", response_model=TourResponse)
async def get_tour(tour_id: int, db: Session = Depends(get_db)):
    """Get a specific tour by ID."""
    try:
        tour = db.query(Tour).filter(Tour.id == tour_id).first()
        if not tour:
            raise HTTPException(status_code=404, detail="Tour not found")
        return tour
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
