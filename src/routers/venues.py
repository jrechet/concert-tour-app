"""Venue listing and detail endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..crud.venue import get_venue_with_upcoming_concerts
from ..database import get_db
from ..schemas.venue import VenueDetailResponse, VenueOut
from ..services.venue_service import list_venues

router = APIRouter(prefix="/api/v1/venues", tags=["venues"])


@router.get("", response_model=List[VenueOut])
def get_venues(
    min_capacity: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve all venues sorted by name ascending.

    When `min_capacity` is provided, only venues with `capacity >=
    min_capacity` are returned. The `ge=0` constraint rejects negative
    values with a 422 before `list_venues` is ever called, so its
    `ValueError` guard for negative input is unreachable from here.
    """
    return list_venues(db, min_capacity=min_capacity)


@router.get("/{venue_id}", response_model=VenueDetailResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Retrieve a single venue with its upcoming, non-cancelled concerts
    ordered soonest-first. Raises 404 when `venue_id` does not exist."""
    venue = get_venue_with_upcoming_concerts(db, venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    return VenueDetailResponse(
        id=venue.id,
        name=venue.name,
        city=venue.city,
        country=venue.country,
        capacity=venue.capacity,
        upcoming_concerts=venue.concerts,
    )
