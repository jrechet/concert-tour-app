"""
Pydantic schemas for Venue entities.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VenueOut(BaseModel):
    """Schema for venue API responses."""

    name: str = Field(..., description="Venue name")
    city: str = Field(..., description="City the venue is located in")
    country: str = Field(..., description="Country the venue is located in")
    capacity: Optional[int] = Field(None, description="Venue capacity")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "Madison Square Garden",
                "city": "New York",
                "country": "USA",
                "capacity": 20000,
            }
        }


class ConcertSummary(BaseModel):
    """Lightweight summary of a concert, embedded in `VenueDetailResponse`.

    `status` and `artist` live on the concert's parent `Tour`
    (`Tour.status`/`Tour.artist`), not on `Concert` itself, so a `Concert`
    ORM object is flattened onto this schema's shape before validation
    rather than relying on `from_attributes` to walk the relationship.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique concert identifier")
    date: datetime = Field(..., description="Concert date and time")
    status: Optional[str] = Field(None, description="Status of the tour this concert belongs to")
    artist: Optional[str] = Field(None, description="Artist performing on the tour this concert belongs to")

    @model_validator(mode="before")
    @classmethod
    def _flatten_concert(cls, data: Any) -> Any:
        """Pass dicts straight through; flatten a `Concert`-like ORM object
        (with a `date_time` field and a `tour` relationship) into this
        schema's flat fields."""
        if isinstance(data, dict):
            return data
        tour = getattr(data, "tour", None)
        return {
            "id": data.id,
            "date": data.date_time,
            "status": getattr(tour, "status", None),
            "artist": getattr(tour, "artist", None),
        }


class VenueDetailResponse(BaseModel):
    """Schema for the venue detail endpoint, with upcoming concerts nested."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique venue identifier")
    name: str = Field(..., description="Venue name")
    city: str = Field(..., description="City the venue is located in")
    country: str = Field(..., description="Country the venue is located in")
    capacity: Optional[int] = Field(None, description="Venue capacity")
    upcoming_concerts: List[ConcertSummary] = Field(
        default_factory=list, description="Upcoming concerts scheduled at this venue"
    )
