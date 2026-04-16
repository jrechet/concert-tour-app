from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from ..models import Venue


def create_venue(db: Session, venue_data: dict) -> Venue:
    """Create a new venue."""
    venue = Venue(**venue_data)
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


def get_venue(db: Session, venue_id: int) -> Optional[Venue]:
    """Get a venue by ID."""
    return db.query(Venue).filter(Venue.id == venue_id).first()


def get_venues(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    city_filter: Optional[str] = None,
    country_filter: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Venue]:
    """Get venues with optional filtering and pagination."""
    query = db.query(Venue)
    
    # Build filter conditions
    filters = []
    
    if city_filter:
        filters.append(Venue.city.ilike(f"%{city_filter}%"))
    
    if country_filter:
        filters.append(Venue.country.ilike(f"%{country_filter}%"))
    
    if search_query:
        filters.append(Venue.name.ilike(f"%{search_query}%"))
    
    # Apply filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply pagination
    return query.offset(offset).limit(limit).all()


def update_venue(db: Session, venue_id: int, venue_data: dict) -> Optional[Venue]:
    """Update a venue by ID."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        return None
    
    # Update venue fields
    for field, value in venue_data.items():
        if hasattr(venue, field):
            setattr(venue, field, value)
    
    db.commit()
    db.refresh(venue)
    return venue


def delete_venue(db: Session, venue_id: int) -> bool:
    """Delete a venue by ID. Returns True if deleted, False if not found."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        return False
    
    db.delete(venue)
    db.commit()
    return True
