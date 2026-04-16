"""Pydantic schemas for API request and response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TourStatus(str, Enum):
    """Tour status enumeration."""
    planning = "planning"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class TourBase(BaseModel):
    """Base schema for Tour."""
    name: str = Field(..., min_length=1, max_length=100, description="Tour name")
    description: Optional[str] = Field(None, max_length=500, description="Tour description")
    start_date: datetime = Field(..., description="Tour start date")
    end_date: Optional[datetime] = Field(None, description="Tour end date")
    status: TourStatus = Field(default=TourStatus.planning, description="Tour status")


class TourCreate(TourBase):
    """Schema for creating a tour."""
    pass


class TourUpdate(BaseModel):
    """Schema for updating a tour."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[TourStatus] = None


class ConcertResponse(BaseModel):
    """Schema for concert response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    venue: str
    city: str
    country: str
    date: datetime
    ticket_price: float
    available_tickets: int
    tour_id: int


class TourResponse(TourBase):
    """Schema for tour response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    concerts: List[ConcertResponse] = Field(default_factory=list)


class ConcertBase(BaseModel):
    """Base schema for Concert."""
    venue: str = Field(..., min_length=1, max_length=200, description="Concert venue")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    country: str = Field(..., min_length=1, max_length=100, description="Country")
    date: datetime = Field(..., description="Concert date")
    ticket_price: float = Field(..., gt=0, description="Ticket price (must be positive)")
    available_tickets: int = Field(..., ge=0, description="Available tickets (cannot be negative)")
    tour_id: int = Field(..., gt=0, description="Tour ID")


class ConcertCreate(ConcertBase):
    """Schema for creating a concert."""
    pass


class ConcertUpdate(BaseModel):
    """Schema for updating a concert."""
    venue: Optional[str] = Field(None, min_length=1, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[datetime] = None
    ticket_price: Optional[float] = Field(None, gt=0)
    available_tickets: Optional[int] = Field(None, ge=0)
