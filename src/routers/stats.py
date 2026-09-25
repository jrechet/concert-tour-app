"""Aggregate stats endpoints for populating filter controls: the distinct
cities and venue names that currently host at least one concert, and the
count of concerts scheduled today or later."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db, get_reference_time
from ..models import Concert, Venue
from ..schemas import CountResponse, UpcomingCountResponse
from ..services.stats_service import get_concert_count, get_upcoming_concert_count

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


@router.get("/count", response_model=CountResponse)
def get_count(db: Session = Depends(get_db)):
    """Retrieve the total number of concerts, regardless of date."""
    return {"count": get_concert_count(db)}


@router.get("/upcoming-count", response_model=UpcomingCountResponse)
def get_upcoming_count(
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve the count of concerts scheduled today or later.

    A concert is upcoming when its calendar date (compared against
    `reference_time`) is today or in the future; past concerts are
    excluded from the count.
    """
    return {"count": get_upcoming_concert_count(db, reference_time)}
