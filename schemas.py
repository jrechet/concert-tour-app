from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TourStatus(str, Enum):
    planning = "planning"
    announced = "announced"
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"


class ConcertStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    sold_out = "sold_out"
    cancelled = "cancelled"
    completed = "completed"


class TourCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    status: TourStatus = TourStatus.planning

    class Config:
        from_attributes = True


class TourResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    status: TourStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConcertCreate(BaseModel):
    tour_id: int
    venue_name: str = Field(..., min_length=1, max_length=200)
    venue_address: str = Field(..., min_length=1, max_length=500)
    venue_city: str = Field(..., min_length=1, max_length=100)
    venue_country: str = Field(..., min_length=1, max_length=100)
    venue_capacity: int = Field(..., gt=0)
    concert_date: datetime
    ticket_price: float = Field(..., gt=0)
    status: ConcertStatus = ConcertStatus.scheduled

    class Config:
        from_attributes = True


class ConcertResponse(BaseModel):
    id: int
    tour_id: int
    venue_name: str
    venue_address: str
    venue_city: str
    venue_country: str
    venue_capacity: int
    concert_date: datetime
    ticket_price: float
    status: ConcertStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
