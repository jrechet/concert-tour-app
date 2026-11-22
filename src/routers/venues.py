"""Venue listing, detail, and creation endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import MIN_SEARCH_QUERY_LENGTH
from ..crud.venue import create_venue, get_venue_with_upcoming_concerts, venue_name_city_exists
from ..database import get_db
from ..schemas.concert import ConcertSummary
from ..schemas.venue import (
    VenueCreate,
    VenueDeleteConflict,
    VenueDetailRead,
    VenueOut,
    VenueRead,
    VenueResponse,
    VenueUpdate,
)
from ..services.venue_service import (
    VenueConflictError,
    VenueHasConcertsError,
    VenueNotFoundError,
    delete_venue,
    get_venue_or_none,
    list_venue_concerts,
    list_venues,
    search_venues,
    update_venue,
)

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


@router.get("/search", response_model=List[VenueRead])
def search_venues_route(
    q: str = Query(..., min_length=MIN_SEARCH_QUERY_LENGTH),
    db: Session = Depends(get_db),
):
    """Search venues whose name or city contains `q` (case-insensitive),
    ordered by name ascending. Returns `[]` when nothing matches."""
    return search_venues(db, q)


@router.get("/{venue_id}", response_model=VenueDetailRead)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Retrieve a single venue with its upcoming, non-cancelled concerts
    ordered soonest-first. Raises 404 when `venue_id` does not exist."""
    venue = get_venue_with_upcoming_concerts(db, venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    return VenueDetailRead(
        id=venue.id,
        name=venue.name,
        city=venue.city,
        country=venue.country,
        capacity=venue.capacity,
        upcoming_concerts=venue.concerts,
    )


@router.patch("/{venue_id}", response_model=VenueResponse)
def patch_venue(venue_id: int, payload: VenueUpdate, db: Session = Depends(get_db)):
    """Apply a partial update to a venue. Raises 404 when `venue_id` does
    not exist, or 409 when the resulting (name, city) pair already
    belongs to a different venue."""
    try:
        return update_venue(db, venue_id, payload)
    except VenueNotFoundError:
        raise HTTPException(status_code=404, detail="Venue not found")
    except VenueConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete(
    "/{venue_id}",
    status_code=204,
    responses={
        204: {"description": "Venue deleted"},
        404: {"description": "Venue not found"},
        409: {"model": VenueDeleteConflict, "description": "Venue still hosts concerts"},
    },
)
def delete_venue_route(venue_id: int, db: Session = Depends(get_db)):
    """Delete a venue. Raises 404 when `venue_id` does not exist, or 409
    when the venue still hosts at least one concert."""
    try:
        delete_venue(db, venue_id)
    except VenueNotFoundError:
        raise HTTPException(status_code=404, detail="Venue not found")
    except VenueHasConcertsError as exc:
        conflict = VenueDeleteConflict(
            detail=f"Venue {venue_id} still hosts {exc.concert_count} concert(s)",
            concert_count=exc.concert_count,
        )
        return JSONResponse(status_code=409, content=conflict.model_dump())


@router.get(
    "/{venue_id}/concerts",
    response_model=List[ConcertSummary],
    summary="List a venue's non-cancelled concerts, soonest first",
)
def get_venue_concerts(venue_id: int, db: Session = Depends(get_db)):
    """Retrieve every non-cancelled concert for a venue, ordered
    soonest-first. Raises 404 when `venue_id` does not exist; an existing
    venue with no matching concerts returns an empty list."""
    if get_venue_or_none(db, venue_id) is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    return list_venue_concerts(db, venue_id)
