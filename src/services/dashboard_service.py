from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date
from ..models.concert import Concert
from ..models.venue import Venue
from ..schemas.dashboard import (
    TourOverviewResponse,
    DashboardStatsResponse,
    UpcomingConcertResponse,
    PaginatedUpcomingConcertsResponse
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_tour_overview(self) -> TourOverviewResponse:
        """Get tour overview including name, dates, and progress percentage."""
        # Get all concerts ordered by date
        concerts = self.db.query(Concert).order_by(Concert.date).all()
        
        if not concerts:
            return TourOverviewResponse(
                tour_name="Concert Tour",
                start_date=None,
                end_date=None,
                progress_percentage=0.0
            )
        
        start_date = concerts[0].date
        end_date = concerts[-1].date
        
        # Calculate progress based on completed concerts
        total_concerts = len(concerts)
        completed_concerts = len([c for c in concerts if c.date < date.today()])
        progress_percentage = (completed_concerts / total_concerts * 100) if total_concerts > 0 else 0.0
        
        return TourOverviewResponse(
            tour_name="World Tour 2024",
            start_date=start_date,
            end_date=end_date,
            progress_percentage=round(progress_percentage, 1)
        )

    def get_dashboard_stats(self) -> DashboardStatsResponse:
        """Get dashboard statistics including totals and revenue estimate."""
        # Get concerts with venue information
        concerts_query = self.db.query(Concert).join(Venue)
        concerts = concerts_query.all()
        
        if not concerts:
            return DashboardStatsResponse(
                total_concerts=0,
                unique_cities=0,
                unique_countries=0,
                total_capacity=0,
                revenue_estimate=0.0
            )
        
        total_concerts = len(concerts)
        
        # Get unique cities and countries
        unique_cities = len(set(concert.venue.city for concert in concerts))
        unique_countries = len(set(concert.venue.country for concert in concerts))
        
        # Calculate total capacity and revenue estimate
        total_capacity = sum(concert.venue.capacity for concert in concerts)
        revenue_estimate = sum(concert.ticket_price * concert.venue.capacity for concert in concerts)
        
        return DashboardStatsResponse(
            total_concerts=total_concerts,
            unique_cities=unique_cities,
            unique_countries=unique_countries,
            total_capacity=total_capacity,
            revenue_estimate=float(revenue_estimate)
        )

    def get_upcoming_concerts(self, limit: int = 10, offset: int = 0) -> PaginatedUpcomingConcertsResponse:
        """Get paginated list of upcoming concerts."""
        today = date.today()
        
        # Get upcoming concerts with venue information
        upcoming_query = (
            self.db.query(Concert)
            .join(Venue)
            .filter(Concert.date >= today)
            .order_by(Concert.date)
        )
        
        # Get total count for pagination
        total = upcoming_query.count()
        
        # Apply pagination
        concerts = upcoming_query.offset(offset).limit(limit).all()
        
        # Convert to response format
        concert_list = [
            UpcomingConcertResponse(
                id=concert.id,
                date=concert.date,
                venue_name=concert.venue.name,
                city=concert.venue.city,
                country=concert.venue.country,
                ticket_price=concert.ticket_price
            )
            for concert in concerts
        ]
        
        return PaginatedUpcomingConcertsResponse(
            concerts=concert_list,
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
