from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.models import Tour, Concert, Venue
from src.schemas.tours import (
    TourOverviewResponse,
    ConcertInfoResponse,
    TourStatsResponse
)
from sqlalchemy import func, text
from datetime import datetime

router = APIRouter(prefix="/api/v1/tours", tags=["tours"])


@router.get("/current", response_model=TourOverviewResponse)
async def get_current_tour(db: Session = Depends(get_db)):
    """Get current active tour overview."""
    # Find the current active tour (assumes one active tour at a time)
    current_tour = db.query(Tour).filter(Tour.is_active == True).first()
    
    if not current_tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active tour found"
        )
    
    # Calculate progress percentage
    total_concerts = db.query(Concert).filter(Concert.tour_id == current_tour.id).count()
    completed_concerts = db.query(Concert).filter(
        Concert.tour_id == current_tour.id,
        Concert.date < datetime.now().date()
    ).count()
    
    progress_percentage = (completed_concerts / total_concerts * 100) if total_concerts > 0 else 0
    
    return TourOverviewResponse(
        id=current_tour.id,
        name=current_tour.name,
        start_date=current_tour.start_date,
        end_date=current_tour.end_date,
        progress_percentage=round(progress_percentage, 2)
    )


@router.get("/{tour_id}/concerts", response_model=List[ConcertInfoResponse])
async def get_tour_concerts(tour_id: int, db: Session = Depends(get_db)):
    """Get upcoming concerts for a specific tour with venue information."""
    # Verify tour exists
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tour not found"
        )
    
    # Get upcoming concerts with venue info
    concerts = db.query(Concert, Venue).join(
        Venue, Concert.venue_id == Venue.id
    ).filter(
        Concert.tour_id == tour_id,
        Concert.date >= datetime.now().date()
    ).order_by(Concert.date).all()
    
    concert_responses = []
    for concert, venue in concerts:
        concert_responses.append(ConcertInfoResponse(
            id=concert.id,
            date=concert.date,
            time=concert.time,
            venue_name=venue.name,
            city=venue.city,
            country=venue.country,
            capacity=venue.capacity
        ))
    
    return concert_responses


@router.get("/{tour_id}/stats", response_model=TourStatsResponse)
async def get_tour_stats(tour_id: int, db: Session = Depends(get_db)):
    """Get aggregated statistics for a specific tour."""
    # Verify tour exists
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tour not found"
        )
    
    # Get basic stats
    total_concerts = db.query(Concert).filter(Concert.tour_id == tour_id).count()
    
    # Get unique cities and countries
    unique_cities = db.query(
        func.count(func.distinct(Venue.city))
    ).join(
        Concert, Venue.id == Concert.venue_id
    ).filter(Concert.tour_id == tour_id).scalar() or 0
    
    unique_countries = db.query(
        func.count(func.distinct(Venue.country))
    ).join(
        Concert, Venue.id == Concert.venue_id
    ).filter(Concert.tour_id == tour_id).scalar() or 0
    
    # Get total capacity
    total_capacity = db.query(
        func.sum(Venue.capacity)
    ).join(
        Concert, Venue.id == Concert.venue_id
    ).filter(Concert.tour_id == tour_id).scalar() or 0
    
    # Calculate revenue estimate (assuming 80% attendance and $100 average ticket)
    average_ticket_price = 100.0
    estimated_attendance_rate = 0.8
    revenue_estimate = total_capacity * average_ticket_price * estimated_attendance_rate
    
    return TourStatsResponse(
        total_concerts=total_concerts,
        unique_cities=unique_cities,
        unique_countries=unique_countries,
        total_capacity=total_capacity,
        revenue_estimate=round(revenue_estimate, 2)
    )
