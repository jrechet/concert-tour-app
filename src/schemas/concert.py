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
    """Schema for concert API responses.

    Field names mirror the actual `Concert` model (a `venue_id` foreign
    key, not a free-text venue/city/country trio). `remaining_tickets`,
    `sold_out`, and `is_almost_sold_out` are derived read-only properties
    computed from the linked venue's capacity and `tickets_sold` — they are
    never accepted as input on `ConcertCreate`/`ConcertUpdate`.
    """

    id: int = Field(..., description="Unique concert identifier")
    tour_id: int = Field(..., description="ID of the tour this concert belongs to")
    venue_id: int = Field(..., description="ID of the venue hosting this concert")
    date_time: datetime = Field(..., description="Concert date and time")
    ticket_price: Optional[Decimal] = Field(None, description="Ticket price")
    tickets_sold: int = Field(..., description="Number of tickets sold so far")
    remaining_tickets: Optional[int] = Field(
        None, description="Tickets still available; null when the venue's capacity is unknown"
    )
    sold_out: bool = Field(..., description="Whether every ticket for this concert has been sold")
    is_almost_sold_out: bool = Field(
        ..., description="Whether fewer than the configured threshold of tickets remain"
    )

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "tour_id": 1,
                "venue_id": 1,
                "date_time": "2024-07-15T20:00:00",
                "ticket_price": "150.00",
                "tickets_sold": 15000,
                "remaining_tickets": 5000,
                "sold_out": False,
                "is_almost_sold_out": True
            }
        }
