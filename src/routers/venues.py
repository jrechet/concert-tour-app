"""Venue management REST API endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models import Venue
from ..schemas import VenueCreate, VenueUpdate, VenueResponse

router = APIRouter(prefix="/api/v1/venues", tags=["venues"])


@router.get("", response_model=List[VenueResponse])
def list_venues(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of venues to return"),
    offset: int = Query(default=0, ge=0, description="Number of venues to skip"),
    city: Optional[str] = Query(default=None, description="Filter by city"),
    country: Optional[str] = Query(default=None, description="Filter by country"),
    search: Optional[str] = Query(default=None, description="Search by venue name"),
    db: Session = Depends(get_db)
):
    """List venues with pagination and optional filters."""
    query = db.query(Venue)
    
    # Apply filters
    filters = []
    if city:
        filters.append(Venue.city.ilike(f"%{city}%"))
    if country:
        filters.append(Venue.country.ilike(f"%{country}%"))
    if search:
        filters.append(Venue.name.ilike(f"%{search}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    venues = query.offset(offset).limit(limit).all()
    return venues


@router.get("/{venue_id}", response_model=VenueResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Get a single venue by ID."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.post("", response_model=VenueResponse, status_code=201)
def create_venue(venue: VenueCreate, db: Session = Depends(get_db)):
    """Create a new venue."""
    db_venue = Venue(**venue.dict())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.put("/{venue_id}", response_model=VenueResponse)
def update_venue(venue_id: int, venue: VenueUpdate, db: Session = Depends(get_db)):
    """Update an existing venue."""
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    update_data = venue.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_venue, field, value)
    
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.delete("/{venue_id}", status_code=204)
def delete_venue(venue_id: int, db: Session = Depends(get_db)):
    """Delete a venue."""
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    db.delete(db_venue)
    db.commit()
    return None
