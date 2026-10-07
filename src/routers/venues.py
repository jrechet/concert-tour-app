"""Venue listing, detail, and creation endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..crud.venue import create_venue, get_venue_with_upcoming_concerts, venue_name_city_exists
from ..database import get_db
from ..schemas.venue import VenueCreate, VenueDetailResponse, VenueOut, VenueResponse
from ..services.venue_service import list_venues

router = APIRouter(prefix="/api/v1/venues", tags=["venues"])


@router.post("", response_model=VenueResponse, status_code=201)
def post_venue(venue: VenueCreate, db: Session = Depends(get_db)):
    """Create a new venue.

    Returns 409 when a venue with the same `name` and `city` already
    exists. The conflict is pre-checked via a query (covering both the
    common case and the test database, which is built from the models
    without running migrations) and, in deployments where the (name,
    city) unique constraint migration has been applied, also caught as a
    fallback `IntegrityError` so a concurrent insert for the same pair
    can never surface as a 500.
    """
    conflict_detail = f"A venue named '{venue.name}' already exists in {venue.city}"

    if venue_name_city_exists(db, venue.name, venue.city):
        raise HTTPException(status_code=409, detail=conflict_detail)

    try:
        return create_venue(db, venue)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=conflict_detail)


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
