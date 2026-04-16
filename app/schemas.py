from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class VenueBase(BaseModel):
    name: str
    city: str
    state: str
    capacity: int


class VenueCreate(VenueBase):
    pass


class Venue(VenueBase):
    id: int

    class Config:
        from_attributes = True


class ConcertBase(BaseModel):
    date: datetime
    venue_id: int
    notes: Optional[str] = None


class ConcertCreate(ConcertBase):
    pass


class Concert(ConcertBase):
    id: int
    venue: Venue

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_concerts: int
    upcoming_concerts: int
    total_venues: int
    total_capacity: int
