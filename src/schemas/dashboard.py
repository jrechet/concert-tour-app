from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from decimal import Decimal


class TourOverviewResponse(BaseModel):
    tour_name: str
    start_date: Optional[date]
    end_date: Optional[date]
    progress_percentage: float

    class Config:
        from_attributes = True


class DashboardStatsResponse(BaseModel):
    total_concerts: int
    unique_cities: int
    unique_countries: int
    total_capacity: int
    revenue_estimate: float

    class Config:
        from_attributes = True


class UpcomingConcertResponse(BaseModel):
    id: int
    date: date
    venue_name: str
    city: str
    country: str
    ticket_price: Decimal

    class Config:
        from_attributes = True


class PaginatedUpcomingConcertsResponse(BaseModel):
    concerts: List[UpcomingConcertResponse]
    total: int
    limit: int
    offset: int
    has_next: bool

    class Config:
        from_attributes = True
