"""Venue service layer for CRUD operations and business logic."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

from ..models import Venue
from ..database import get_db


class VenueServiceError(Exception):
    """Custom exception for venue service errors."""
    pass


def create_venue(venue_data: Dict[str, Any]) -> Venue:
    """
    Create a new venue.
    
    Args:
        venue_data: Dictionary containing venue information
        
    Returns:
        Created venue object
        
    Raises:
        VenueServiceError: If creation fails
    """
    db = next(get_db())
    try:
        venue = Venue(**venue_data)
        db.add(venue)
        db.commit()
        db.refresh(venue)
        return venue
    except SQLAlchemyError as e:
        db.rollback()
        raise VenueServiceError(f"Failed to create venue: {str(e)}")
    finally:
        db.close()


def get_venue_by_id(venue_id: int) -> Optional[Venue]:
    """
    Get a venue by its ID.
    
    Args:
        venue_id: The venue ID
        
    Returns:
        Venue object if found, None otherwise
        
    Raises:
        VenueServiceError: If database error occurs
    """
    db = next(get_db())
    try:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        return venue
    except SQLAlchemyError as e:
        raise VenueServiceError(f"Failed to get venue: {str(e)}")
    finally:
        db.close()


def update_venue(venue_id: int, venue_data: Dict[str, Any]) -> Optional[Venue]:
    """
    Update a venue.
    
    Args:
        venue_id: The venue ID to update
        venue_data: Dictionary containing updated venue information
        
    Returns:
        Updated venue object if found, None otherwise
        
    Raises:
        VenueServiceError: If update fails
    """
    db = next(get_db())
    try:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if not venue:
            return None
            
        for key, value in venue_data.items():
            if hasattr(venue, key):
                setattr(venue, key, value)
                
        db.commit()
        db.refresh(venue)
        return venue
    except SQLAlchemyError as e:
        db.rollback()
        raise VenueServiceError(f"Failed to update venue: {str(e)}")
    finally:
        db.close()


def delete_venue(venue_id: int) -> bool:
    """
    Delete a venue.
    
    Args:
        venue_id: The venue ID to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        VenueServiceError: If deletion fails
    """
    db = next(get_db())
    try:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if not venue:
            return False
            
        db.delete(venue)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise VenueServiceError(f"Failed to delete venue: {str(e)}")
    finally:
        db.close()


def list_venues(
    search_term: Optional[str] = None,
    city_filter: Optional[str] = None,
    min_capacity: Optional[int] = None
) -> List[Venue]:
    """
    List venues with optional filtering and search.
    
    Args:
        search_term: Search for venues matching name or city
        city_filter: Filter by specific city
        min_capacity: Filter by minimum capacity
        
    Returns:
        List of venues matching criteria
        
    Raises:
        VenueServiceError: If query fails
    """
    db = next(get_db())
    try:
        query = db.query(Venue)
        
        # Apply search filter (name or city contains search term)
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Venue.name.ilike(search_pattern),
                    Venue.city.ilike(search_pattern)
                )
            )
        
        # Apply city filter
        if city_filter:
            query = query.filter(Venue.city.ilike(f"%{city_filter}%"))
            
        # Apply minimum capacity filter
        if min_capacity is not None:
            query = query.filter(Venue.capacity >= min_capacity)
            
        venues = query.order_by(Venue.name).all()
        return venues
    except SQLAlchemyError as e:
        raise VenueServiceError(f"Failed to list venues: {str(e)}")
    finally:
        db.close()
