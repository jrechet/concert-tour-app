"""Dashboard API endpoints for HTMX integration."""

from datetime import datetime, date
from typing import Dict, Any, Optional
from decimal import Decimal
import calendar

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from src.database import get_db
from src.models import Tour, Concert, Venue, Ticket


router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/tour-overview")
async def get_tour_overview(
    tour_id: Optional[int] = Query(None, description="Tour ID to get overview for"),
    db: Session = Depends(get_db)
):
    """Get tour overview data for dashboard."""
    # Get the current active tour if no tour_id specified
    if tour_id is None:
        tour = db.query(Tour).filter(Tour.status == "active").first()
    else:
        tour = db.query(Tour).filter(Tour.id == tour_id).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    # Get concert count and date range
    concerts = db.query(Concert).filter(Concert.tour_id == tour.id).all()
    
    total_concerts = len(concerts)
    completed_concerts = len([c for c in concerts if c.status == "completed"])
    
    # Calculate progress
    progress = (completed_concerts / total_concerts * 100) if total_concerts > 0 else 0
    
    # Get date range
    start_date = min([c.date for c in concerts]) if concerts else tour.start_date
    end_date = max([c.date for c in concerts]) if concerts else tour.end_date
    
    return {
        "id": tour.id,
        "name": tour.name,
        "description": tour.description,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "status": tour.status,
        "total_concerts": total_concerts,
        "completed_concerts": completed_concerts,
        "progress": round(progress, 1)
    }


@router.get("/statistics")
async def get_dashboard_statistics(
    tour_id: Optional[int] = Query(None, description="Tour ID to get statistics for"),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for metrics cards."""
    # Get the current active tour if no tour_id specified
    if tour_id is None:
        tour = db.query(Tour).filter(Tour.status == "active").first()
        if not tour:
            raise HTTPException(status_code=404, detail="No active tour found")
        tour_id = tour.id
    
    # Get concerts for the tour
    concerts_query = db.query(Concert).filter(Concert.tour_id == tour_id)
    
    # Total concerts
    total_concerts = concerts_query.count()
    
    # Unique cities count
    unique_cities = db.query(func.count(func.distinct(Venue.city))).join(
        Concert, Concert.venue_id == Venue.id
    ).filter(Concert.tour_id == tour_id).scalar() or 0
    
    # Unique countries count
    unique_countries = db.query(func.count(func.distinct(Venue.country))).join(
        Concert, Concert.venue_id == Venue.id
    ).filter(Concert.tour_id == tour_id).scalar() or 0
    
    # Total capacity
    total_capacity = db.query(func.sum(Venue.capacity)).join(
        Concert, Concert.venue_id == Venue.id
    ).filter(Concert.tour_id == tour_id).scalar() or 0
    
    # Total revenue from tickets
    total_revenue = db.query(func.sum(Ticket.price)).join(
        Concert, Ticket.concert_id == Concert.id
    ).filter(Concert.tour_id == tour_id).scalar() or 0
    
    # Convert Decimal to float for JSON serialization
    if isinstance(total_revenue, Decimal):
        total_revenue = float(total_revenue)
    
    return {
        "concerts": total_concerts,
        "cities": unique_cities,
        "countries": unique_countries,
        "capacity": total_capacity,
        "revenue": total_revenue
    }


@router.get("/calendar")
async def get_calendar_data(
    year: int = Query(..., description="Year for calendar view"),
    month: int = Query(..., description="Month for calendar view (1-12)"),
    tour_id: Optional[int] = Query(None, description="Tour ID to filter concerts"),
    db: Session = Depends(get_db)
):
    """Get calendar data for monthly concert view with pagination."""
    # Validate month
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    # Get the current active tour if no tour_id specified
    if tour_id is None:
        tour = db.query(Tour).filter(Tour.status == "active").first()
        if tour:
            tour_id = tour.id
    
    # Build query
    concerts_query = db.query(Concert).join(Venue)
    
    if tour_id:
        concerts_query = concerts_query.filter(Concert.tour_id == tour_id)
    
    # Filter by year and month
    concerts_query = concerts_query.filter(
        extract('year', Concert.date) == year,
        extract('month', Concert.date) == month
    )
    
    concerts = concerts_query.all()
    
    # Get calendar structure
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    month_days = list(cal.itermonthdates(year, month))
    
    # Group concerts by date
    concerts_by_date = {}
    for concert in concerts:
        date_str = concert.date.isoformat()
        if date_str not in concerts_by_date:
            concerts_by_date[date_str] = []
        
        concerts_by_date[date_str].append({
            "id": concert.id,
            "venue_name": concert.venue.name,
            "venue_city": concert.venue.city,
            "status": concert.status,
            "time": concert.date.strftime("%H:%M") if concert.date else None
        })
    
    # Build calendar weeks
    weeks = []
    week = []
    
    for day in month_days:
        day_data = {
            "date": day.isoformat(),
            "day": day.day,
            "is_current_month": day.month == month,
            "concerts": concerts_by_date.get(day.isoformat(), [])
        }
        
        week.append(day_data)
        
        if len(week) == 7:
            weeks.append(week)
            week = []
    
    # Add partial week if needed
    if week:
        weeks.append(week)
    
    # Calculate pagination info
    current_date = date(year, month, 1)
    
    # Previous month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    # Next month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    return {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "weeks": weeks,
        "pagination": {
            "prev": {
                "year": prev_year,
                "month": prev_month,
                "month_name": calendar.month_name[prev_month]
            },
            "next": {
                "year": next_year,
                "month": next_month,
                "month_name": calendar.month_name[next_month]
            }
        },
        "total_concerts": len(concerts)
    }
