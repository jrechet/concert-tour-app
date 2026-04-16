from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class VenueBase(BaseModel):
    name: str
    city: str
    state: str
    capacity: Optional[int] = None


class VenueCreate(VenueBase):
    pass


class VenueUpdate(VenueBase):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class VenueResponse(VenueBase):
    id: int

    class Config:
        from_attributes = True


class ConcertBase(BaseModel):
    date: datetime
    venue_id: int
    ticket_price: Optional[float] = None
    notes: Optional[str] = None


class ConcertCreate(ConcertBase):
    pass


class ConcertUpdate(BaseModel):
    date: Optional[datetime] = None
    venue_id: Optional[int] = None
    ticket_price: Optional[float] = None
    notes: Optional[str] = None


class ConcertResponse(ConcertBase):
    id: int
    venue: VenueResponse

    class Config:
        from_attributes = True


class SongBase(BaseModel):
    title: str
    artist: str
    duration_minutes: Optional[float] = None


class SongCreate(SongBase):
    pass


class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    duration_minutes: Optional[float] = None


class SongResponse(SongBase):
    id: int

    class Config:
        from_attributes = True


class SetlistSong(BaseModel):
    id: int
    title: str
    artist: str
    duration_minutes: Optional[float]
    order_position: int


class SetlistResponse(BaseModel):
    concert_id: int
    songs: List[SetlistSong]
    total_duration_minutes: float


class SetlistCreate(BaseModel):
    song_id: int


class SetlistReorder(BaseModel):
    new_position: int
