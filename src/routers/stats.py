"""Aggregate stats endpoints for populating filter controls: the distinct
cities and venue names that currently host at least one concert."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Concert, Venue

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/cities", response_model=List[str])
def get_stats_cities(db: Session = Depends(get_db)):
    """Retrieve the distinct list of cities hosting at least one concert,
    sorted alphabetically.
    """
    rows = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .distinct()
        .order_by(Venue.city)
        .all()
    )
    return [row[0] for row in rows]


@router.get("/venues", response_model=List[str])
def get_stats_venues(db: Session = Depends(get_db)):
    """Retrieve the distinct list of venue names hosting at least one
    concert, sorted alphabetically.
    """
    rows = (
        db.query(Venue.name)
        .join(Concert, Concert.venue_id == Venue.id)
        .distinct()
        .order_by(Venue.name)
        .all()
    )
    return [row[0] for row in rows]
