from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import Concert, Tour
from ..schemas import ConcertCreate, ConcertUpdate, ConcertResponse

router = APIRouter(prefix="/api/v1/concerts", tags=["concerts"])


@router.post("/", response_model=ConcertResponse, status_code=status.HTTP_201_CREATED)
def create_concert(concert: ConcertCreate, db: Session = Depends(get_db)):
    """Create a new concert."""
    # Verify that the tour exists
    tour = db.query(Tour).filter(Tour.id == concert.tour_id).first()
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tour not found"
        )
    
    try:
        db_concert = Concert(**concert.model_dump())
        db.add(db_concert)
        db.commit()
        db.refresh(db_concert)
        return db_concert
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )


@router.get("/", response_model=List[ConcertResponse])
def get_concerts(tour_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all concerts, optionally filtered by tour_id."""
    query = db.query(Concert)
    if tour_id is not None:
        query = query.filter(Concert.tour_id == tour_id)
    concerts = query.all()
    return concerts


@router.get("/{concert_id}", response_model=ConcertResponse)
def get_concert(concert_id: int, db: Session = Depends(get_db)):
    """Get a specific concert by ID."""
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concert not found"
        )
    return concert


@router.put("/{concert_id}", response_model=ConcertResponse)
def update_concert(concert_id: int, concert_update: ConcertUpdate, db: Session = Depends(get_db)):
    """Update an existing concert."""
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concert not found"
        )
    
    # If tour_id is being updated, verify the new tour exists
    if concert_update.tour_id is not None:
        tour = db.query(Tour).filter(Tour.id == concert_update.tour_id).first()
        if not tour:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tour not found"
            )
    
    try:
        update_data = concert_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(concert, field, value)
        
        db.commit()
        db.refresh(concert)
        return concert
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )


@router.delete("/{concert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concert(concert_id: int, db: Session = Depends(get_db)):
    """Delete a concert."""
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concert not found"
        )
    
    db.delete(concert)
    db.commit()
