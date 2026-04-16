from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional
import math

from src.database import get_db
from src.models import Venue
from src.schemas.venues import (
    VenueCreate,
    VenueUpdate,
    VenueResponse,
    VenueListParams,
    VenueListResponse,
)

router = APIRouter(prefix="/api/v1/venues", tags=["venues"])


@router.post("/", response_model=VenueResponse, status_code=201)
def create_venue(venue_data: VenueCreate, db: Session = Depends(get_db)):
    """Create a new venue."""
    try:
        venue = Venue(
            name=venue_data.name,
            city=venue_data.city,
            address=venue_data.address,
            capacity=venue_data.capacity,
        )
        db.add(venue)
        db.commit()
        db.refresh(venue)
        return venue
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create venue")


@router.get("/{venue_id}", response_model=VenueResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Get a venue by ID."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue with ID {venue_id} not found")
    return venue


@router.put("/{venue_id}", response_model=VenueResponse)
def update_venue(venue_id: int, venue_data: VenueUpdate, db: Session = Depends(get_db)):
    """Update a venue by ID."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue with ID {venue_id} not found")
    
    try:
        # Update only provided fields
        update_data = venue_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(venue, field, value)
        
        db.commit()
        db.refresh(venue)
        return venue
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update venue")


@router.delete("/{venue_id}", status_code=204)
def delete_venue(venue_id: int, db: Session = Depends(get_db)):
    """Delete a venue by ID."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue with ID {venue_id} not found")
    
    try:
        db.delete(venue)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete venue")


@router.get("/", response_model=VenueListResponse)
def list_venues(
    search: Optional[str] = Query(None, description="Search in venue name or city"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_capacity: Optional[int] = Query(None, ge=1, description="Minimum capacity filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List venues with optional filtering and pagination."""
    query = db.query(Venue)
    
    # Apply filters
    filters = []
    
    if search:
        search_filter = or_(
            Venue.name.ilike(f"%{search}%"),
            Venue.city.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if city:
        filters.append(Venue.city.ilike(f"%{city}%"))
    
    if min_capacity:
        filters.append(Venue.capacity >= min_capacity)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    venues = query.offset(offset).limit(page_size).all()
    
    # Calculate pagination info
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return VenueListResponse(
        venues=venues,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
