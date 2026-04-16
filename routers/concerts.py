from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Concert, Tour
from schemas import ConcertCreate, ConcertResponse

router = APIRouter(prefix="/api/v1/concerts", tags=["concerts"])


@router.get("", response_model=List[ConcertResponse])
async def get_concerts(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Get concerts with pagination."""
    try:
        concerts = db.query(Concert).offset(offset).limit(limit).all()
        return concerts
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=ConcertResponse, status_code=201)
async def create_concert(concert: ConcertCreate, db: Session = Depends(get_db)):
    """Create a new concert."""
    try:
        # Validate that the tour exists
        tour = db.query(Tour).filter(Tour.id == concert.tour_id).first()
        if not tour:
            raise HTTPException(status_code=400, detail="Tour not found")
        
        db_concert = Concert(**concert.dict())
        db.add(db_concert)
        db.commit()
        db.refresh(db_concert)
        return db_concert
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create concert")


@router.get("/{concert_id}", response_model=ConcertResponse)
async def get_concert(concert_id: int, db: Session = Depends(get_db)):
    """Get a specific concert by ID."""
    try:
        concert = db.query(Concert).filter(Concert.id == concert_id).first()
        if not concert:
            raise HTTPException(status_code=404, detail="Concert not found")
        return concert
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
