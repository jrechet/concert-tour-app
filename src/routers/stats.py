"""Read-only aggregate stats endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Concert, Venue
from ..schemas import CitiesResponse, VenuesResponse

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


def get_distinct_cities(db: Session) -> list:
    """Retrieve the distinct list of cities hosting at least one concert,
    sorted alphabetically. Returns an empty list when there is no data."""
    rows = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .distinct()
        .order_by(Venue.city)
        .all()
    )
    return [row[0] for row in rows]


def get_distinct_venue_names(db: Session) -> list:
    """Retrieve the distinct list of venue names hosting at least one concert,
    sorted alphabetically. Returns an empty list when there is no data."""
    rows = (
        db.query(Venue.name)
        .join(Concert, Concert.venue_id == Venue.id)
        .distinct()
        .order_by(Venue.name)
        .all()
    )
    return [row[0] for row in rows]


@router.get("/cities", response_model=CitiesResponse)
def get_cities_stats(db: Session = Depends(get_db)):
    """Retrieve the distinct, sorted list of cities with at least one concert.

    Returns 200 with an empty list (not an error) when there is no data.
    """
    return CitiesResponse(cities=get_distinct_cities(db))


@router.get("/venues", response_model=VenuesResponse)
def get_venues_stats(db: Session = Depends(get_db)):
    """Retrieve the distinct, sorted list of venue names with at least one concert.

    Returns 200 with an empty list (not an error) when there is no data.
    """
    return VenuesResponse(venues=get_distinct_venue_names(db))
