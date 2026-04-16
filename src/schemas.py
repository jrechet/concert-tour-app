from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class TourStatus(str, Enum):
    planning = "planning"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class ConcertStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class TicketStatus(str, Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"
    cancelled = "cancelled"


class TourBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TourStatus = TourStatus.planning
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TourCreate(TourBase):
    pass


class Tour(TourBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class VenueBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., gt=0)


class VenueCreate(VenueBase):
    pass


class Venue(VenueBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class ConcertBase(BaseModel):
    tour_id: int
    venue_id: int
    date: datetime
    doors_open: Optional[datetime] = None
    show_start: Optional[datetime] = None
    status: ConcertStatus = ConcertStatus.scheduled
    base_price: Decimal = Field(..., gt=0)


class ConcertCreate(ConcertBase):
    pass


class Concert(ConcertBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class TicketBase(BaseModel):
    concert_id: int
    seat_number: Optional[str] = None
    section: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    status: TicketStatus = TicketStatus.available
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class TicketCreate(TicketBase):
    pass


class Ticket(TicketBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    purchased_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DashboardStats(BaseModel):
    total_tours: int
    active_tours: int
    total_concerts: int
    upcoming_concerts: int
    completed_concerts: int
    total_tickets: int
    sold_tickets: int
    available_tickets: int
    total_revenue: Decimal
    total_venues: int


class TourProgress(BaseModel):
    tour_id: int
    tour_name: str
    total_concerts: int
    completed_concerts: int
    upcoming_concerts: int
    progress_percentage: float
    total_tickets: int
    sold_tickets: int
    revenue: Decimal
