"""
Pydantic schemas for Tour entities.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class TourStatus(str, Enum):
    """Valid values for `Tour.status`, used for query-parameter validation."""

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


class TourCreate(BaseModel):
    """Schema for creating a new tour."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Tour name")
    artist: str = Field(..., min_length=1, max_length=100, description="Artist name")
    start_date: date = Field(..., description="Tour start date")
    end_date: date = Field(..., description="Tour end date")
    description: Optional[str] = Field(None, max_length=1000, description="Tour description")
    status: Optional[str] = Field("planned", max_length=50, description="Tour status")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Ensure end_date is not before start_date."""
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after or equal to start_date')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "World Tour 2024",
                "artist": "The Beatles",
                "start_date": "2024-06-01",
                "end_date": "2024-12-31",
                "description": "An amazing world tour featuring classic hits"
            }
        }


class TourUpdate(BaseModel):
    """Schema for updating an existing tour."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Tour name")
    artist: Optional[str] = Field(None, min_length=1, max_length=100, description="Artist name")
    start_date: Optional[date] = Field(None, description="Tour start date")
    end_date: Optional[date] = Field(None, description="Tour end date")
    description: Optional[str] = Field(None, max_length=1000, description="Tour description")
    status: Optional[str] = Field(None, max_length=50, description="Tour status")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Ensure end_date is not before start_date if both are provided."""
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError('end_date must be after or equal to start_date')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "Updated World Tour 2024",
                "description": "Updated description for the tour"
            }
        }


class TourResponse(BaseModel):
    """Schema for tour API responses."""
    
    id: int = Field(..., description="Unique tour identifier")
    name: str = Field(..., description="Tour name")
    artist: str = Field(..., description="Artist name")
    start_date: date = Field(..., description="Tour start date")
    end_date: date = Field(..., description="Tour end date")
    description: Optional[str] = Field(None, description="Tour description")
    status: Optional[str] = Field(None, description="Tour status")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "World Tour 2024",
                "artist": "The Beatles",
                "start_date": "2024-06-01",
                "end_date": "2024-12-31",
                "description": "An amazing world tour featuring classic hits"
            }
        }


class TourSummary(BaseModel):
    """Schema for the tour summary API response."""

    tour_id: int = Field(..., description="Unique tour identifier")
    date_count: int = Field(..., description="Number of tour dates")
    first_date: Optional[date] = Field(None, description="Earliest tour date")
    last_date: Optional[date] = Field(None, description="Latest tour date")
    distinct_city_count: int = Field(..., description="Number of distinct cities visited")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "tour_id": 1,
                "date_count": 12,
                "first_date": "2024-06-01",
                "last_date": "2024-12-31",
                "distinct_city_count": 9
            }
        }


class TourCitiesResponse(BaseModel):
    """Schema for the tour cities API response."""

    tour_id: int = Field(..., description="Unique tour identifier")
    cities: List[str] = Field(..., description="Distinct cities visited, in date order")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "tour_id": 1,
                "cities": ["New York", "London", "Paris"]
            }
        }


class CancelTourRequest(BaseModel):
    """Schema for requesting cancellation of a tour."""

    reason: str = Field(..., min_length=1, description="Reason for cancelling the tour")

    @validator('reason')
    def validate_reason_not_blank(cls, v):
        """Reject a reason that is only whitespace, and trim surrounding
        whitespace from valid ones."""
        trimmed = v.strip()
        if not trimmed:
            raise ValueError('reason must not be blank')
        return trimmed

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "reason": "Artist illness"
            }
        }


class CancelTourResponse(BaseModel):
    """Schema for the tour cancellation API response."""

    cancelled_count: int = Field(..., description="Number of concerts cancelled")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "cancelled_count": 5
            }
        }


class TourSpanResponse(BaseModel):
    """Schema for the tour span API response."""

    first_date: Optional[date] = Field(None, description="Earliest non-cancelled concert date")
    last_date: Optional[date] = Field(None, description="Latest non-cancelled concert date")
    days_between: Optional[int] = Field(None, description="Number of calendar days between first_date and last_date")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "first_date": "2024-06-01",
                "last_date": "2024-12-31",
                "days_between": 213
            }
        }


class TourOccupancyResponse(BaseModel):
    """Schema for the tour occupancy API response."""

    tickets_sold: int = Field(..., description="Tickets sold across the tour's non-cancelled concerts")
    total_capacity: int = Field(..., description="Total venue capacity across the tour's non-cancelled concerts")
    percentage_sold: float = Field(..., description="Tickets sold as a percentage of total capacity, rounded to 2 decimal places")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "tickets_sold": 24000,
                "total_capacity": 30000,
                "percentage_sold": 80.0,
            }
        }


class TourRevenue(BaseModel):
    """Schema for the tour revenue API response."""

    revenue: Decimal = Field(..., description="Total ticket revenue for the tour")
    concert_count: int = Field(..., description="Number of concerts the revenue was summed over")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "revenue": "13000.00",
                "concert_count": 2
            }
        }
