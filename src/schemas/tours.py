from pydantic import BaseModel
from datetime import date, time
from typing import Optional


class TourOverviewResponse(BaseModel):
    """Schema for current tour overview response."""
    id: int
    name: str
    start_date: date
    end_date: date
    progress_percentage: float
    
    class Config:
        from_attributes = True


class ConcertInfoResponse(BaseModel):
    """Schema for concert information with venue details."""
    id: int
    date: date
    time: Optional[time] = None
    venue_name: str
    city: str
    country: str
    capacity: int
    
    class Config:
        from_attributes = True


class TourStatsResponse(BaseModel):
    """Schema for tour statistics response."""
    total_concerts: int
    unique_cities: int
    unique_countries: int
    total_capacity: int
    revenue_estimate: float
    
    class Config:
        from_attributes = True
