"""Aggregate stats endpoints for populating filter controls: the distinct
cities and venue names that currently host at least one concert, and the
count of concerts scheduled today or later."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db, get_reference_time
from ..schemas import (
    CitiesResponse,
    CountResponse,
    CountryConcertCount,
    MonthlyConcertCount,
    UpcomingCountResponse,
    VenuesResponse,
)
from ..services.stats_service import (
    get_concert_count,
    get_concert_counts_by_country,
    get_concert_counts_by_month,
    get_distinct_cities,
    get_distinct_venue_names,
    get_upcoming_concert_count,
)

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


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


@router.get("/count", response_model=CountResponse)
def get_count(db: Session = Depends(get_db)):
    """Retrieve the total number of concerts, regardless of date."""
    return {"count": get_concert_count(db)}


@router.get("/countries", response_model=List[CountryConcertCount])
def get_countries_stats(db: Session = Depends(get_db)):
    """Retrieve the number of non-cancelled concerts per country, ordered by
    concert count descending.

    Cancelled concerts are excluded from the counts. A country with zero
    non-cancelled concerts (or no concerts at all) is omitted from the
    response rather than appearing with a count of 0.
    """
    return [
        CountryConcertCount(country=country, concert_count=count)
        for country, count in get_concert_counts_by_country(db)
    ]


@router.get("/months", response_model=List[MonthlyConcertCount])
def get_months_stats(db: Session = Depends(get_db)):
    """Retrieve the number of non-cancelled concerts per calendar month,
    ordered chronologically ascending.

    Cancelled concerts are excluded from the counts. A month with zero
    non-cancelled concerts is omitted from the response rather than
    appearing with a count of 0.
    """
    return [
        MonthlyConcertCount(month=month, count=count)
        for month, count in get_concert_counts_by_month(db)
    ]


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
