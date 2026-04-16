"""Pydantic schemas for request/response validation."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# Base schemas
class VenueBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Venue name")
    address: str = Field(..., min_length=1, max_length=500, description="Venue address")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    country: str = Field(..., min_length=1, max_length=100, description="Country")
    capacity: int = Field(..., gt=0, description="Venue capacity")


class VenueCreate(VenueBase):
    pass


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Venue name")
    address: Optional[str] = Field(None, min_length=1, max_length=500, description="Venue address")
    city: Optional[str] = Field(None, min_length=1, max_length=100, description="City")
    country: Optional[str] = Field(None, min_length=1, max_length=100, description="Country")
    capacity: Optional[int] = Field(None, gt=0, description="Venue capacity")


class VenueResponse(VenueBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Artist schemas
class ArtistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Artist name")
    genre: str = Field(..., min_length=1, max_length=100, description="Music genre")
    description: Optional[str] = Field(None, max_length=1000, description="Artist description")


class ArtistCreate(ArtistBase):
    pass


class ArtistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Artist name")
    genre: Optional[str] = Field(None, min_length=1, max_length=100, description="Music genre")
    description: Optional[str] = Field(None, max_length=1000, description="Artist description")


class ArtistResponse(ArtistBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Concert schemas
class ConcertBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Concert title")
    date: date = Field(..., description="Concert date")
    ticket_price: float = Field(..., gt=0, description="Ticket price")
    artist_id: int = Field(..., description="Artist ID")
    venue_id: int = Field(..., description="Venue ID")


class ConcertCreate(ConcertBase):
    pass


class ConcertUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Concert title")
    date: Optional[date] = Field(None, description="Concert date")
    ticket_price: Optional[float] = Field(None, gt=0, description="Ticket price")
    artist_id: Optional[int] = Field(None, description="Artist ID")
    venue_id: Optional[int] = Field(None, description="Venue ID")


class ConcertResponse(ConcertBase):
    id: int
    created_at: datetime
    updated_at: datetime
    artist: ArtistResponse
    venue: VenueResponse

    class Config:
        orm_mode = True
