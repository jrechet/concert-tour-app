"""
Pydantic schemas for Concert entities.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class ConcertCreate(BaseModel):
    """Schema for creating a new concert."""
    
    tour_id: int = Field(..., gt=0, description="ID of the tour this concert belongs to")
    venue: str = Field(..., min_length=1, max_length=200, description="Concert venue name")
    city: str = Field(..., min_length=1, max_length=100, description="City where concert takes place")
    country: str = Field(..., min_length=1, max_length=100, description="Country where concert takes place")
    date_time: datetime = Field(..., description="Concert date and time")
    ticket_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Ticket price")
    capacity: Optional[int] = Field(None, gt=0, description="Venue capacity")
    
    @validator('date_time')
    def validate_future_date(cls, v):
        """Ensure concert date is in the future."""
        if v <= datetime.now():
            raise ValueError('Concert date must be in the future')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "tour_id": 1,
                "venue": "Madison Square Garden",
                "city": "New York",
                "country": "USA",
                "date_time": "2024-07-15T20:00:00",
                "ticket_price": "150.00",
                "capacity": 20000
            }
        }


class ConcertUpdate(BaseModel):
    """Schema for updating an existing concert."""
    
    tour_id: Optional[int] = Field(None, gt=0, description="ID of the tour this concert belongs to")
    venue: Optional[str] = Field(None, min_length=1, max_length=200, description="Concert venue name")
    city: Optional[str] = Field(None, min_length=1, max_length=100, description="City where concert takes place")
    country: Optional[str] = Field(None, min_length=1, max_length=100, description="Country where concert takes place")
    date_time: Optional[datetime] = Field(None, description="Concert date and time")
    ticket_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Ticket price")
    capacity: Optional[int] = Field(None, gt=0, description="Venue capacity")
    
    @validator('date_time')
    def validate_future_date(cls, v):
        """Ensure concert date is in the future if provided."""
        if v is not None and v <= datetime.now():
            raise ValueError('Concert date must be in the future')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "venue": "Updated Venue Name",
                "ticket_price": "175.00"
            }
        }


class ConcertResponse(BaseModel):
    """Schema for concert API responses."""
    
    id: int = Field(..., description="Unique concert identifier")
    tour_id: int = Field(..., description="ID of the tour this concert belongs to")
    venue: str = Field(..., description="Concert venue name")
    city: str = Field(..., description="City where concert takes place")
    country: str = Field(..., description="Country where concert takes place")
    date_time: datetime = Field(..., description="Concert date and time")
    ticket_price: Optional[Decimal] = Field(None, description="Ticket price")
    capacity: Optional[int] = Field(None, description="Venue capacity")
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "tour_id": 1,
                "venue": "Madison Square Garden",
                "city": "New York",
                "country": "USA",
                "date_time": "2024-07-15T20:00:00",
                "ticket_price": "150.00",
                "capacity": 20000
            }
        }
