"""
Pydantic schemas for Venue entities.
"""

from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from ..config import MIN_SEARCH_QUERY_LENGTH
from .tour import TourStatus

MIN_VENUE_CAPACITY = 0


class VenueCreate(BaseModel):
    """Schema for creating a venue."""

    name: str = Field(..., min_length=1, description="Venue name")
    city: str = Field(..., description="City the venue is located in")
    country: str = Field(..., description="Country the venue is located in")
    capacity: int = Field(..., gt=MIN_VENUE_CAPACITY, description="Venue capacity")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Reject whitespace-only names."""
        if not v.strip():
            raise ValueError("name must not be empty or whitespace")
        return v


class VenueUpdate(BaseModel):
    """Schema for the request body of `PATCH /api/v1/venues/{id}`.

    Every field is optional so any subset may be sent, but at least one must
    actually be set: an entirely empty/null body is rejected so a no-op PATCH
    doesn't silently return 200.
    """

    name: Optional[str] = Field(None, min_length=1, description="Venue name")
    city: Optional[str] = Field(None, description="City the venue is located in")
    country: Optional[str] = Field(None, description="Country the venue is located in")
    capacity: Optional[int] = Field(None, gt=MIN_VENUE_CAPACITY, description="Venue capacity")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        """Reject a whitespace-only name, while still allowing `None` (field omitted)."""
        if v is not None and not v.strip():
            raise ValueError("name must not be empty or whitespace")
        return v

    @model_validator(mode="after")
    def at_least_one_field_must_be_set(self) -> "VenueUpdate":
        """Reject a body where every field is omitted or null."""
        if self.name is None and self.city is None and self.country is None and self.capacity is None:
            raise ValueError("at least one field must be provided")
        return self


class VenueRead(BaseModel):
    """Schema for reading a venue, serialized from an ORM instance."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique venue identifier")
    name: str = Field(..., description="Venue name")
    city: str = Field(..., description="City the venue is located in")
    country: str = Field(..., description="Country the venue is located in")
    capacity: int = Field(..., description="Venue capacity")


class VenueResponse(BaseModel):
    """Schema for venue API responses, including the database id."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique venue identifier")
    name: str = Field(..., description="Venue name")
    city: str = Field(..., description="City the venue is located in")
    country: str = Field(..., description="Country the venue is located in")
    capacity: int = Field(..., ge=0, description="Venue capacity")


class VenueDeleteConflict(BaseModel):
    """Schema for the 409 response when a venue cannot be deleted because
    it still hosts concerts."""

    detail: str = Field(..., description="Human-readable explanation of the conflict")
    concert_count: int = Field(..., ge=0, description="Number of concerts hosted by this venue")


class VenueListParams(BaseModel):
    """Query parameters accepted by `GET /api/v1/venues`."""

    min_capacity: Optional[int] = Field(None, description="Only return venues with at least this capacity")

    @field_validator("min_capacity")
    @classmethod
    def min_capacity_must_not_be_negative(cls, v: Optional[int]) -> Optional[int]:
        """Reject negative values."""
        if v is not None and v < 0:
            raise ValueError("min_capacity must not be negative")
        return v


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


class VenueConcertRead(BaseModel):
    """Read-only schema for a concert nested under `VenueDetailRead.upcoming_concerts`.

    `title` and `status` are sourced from the concert's parent `Tour`
    (`Concert` has no `title` or `status` column of its own), via
    `AliasPath` so a real `Concert` ORM object validates directly.
    `status` reuses `TourStatus` (the only concert/tour status enum defined
    in the codebase, under `src.schemas.tour`) instead of redeclaring the
    valid status strings here.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., description="Unique concert identifier")
    title: str = Field(
        ..., validation_alias=AliasPath("tour", "name"), description="Title of the tour this concert belongs to"
    )
    start_datetime: datetime = Field(
        ..., validation_alias="date_time", description="Concert start date and time"
    )
    status: Optional[TourStatus] = Field(
        None,
        validation_alias=AliasPath("tour", "status"),
        description="Status of the parent tour this concert belongs to",
    )


class VenueDetailRead(BaseModel):
    """Read-only schema for the venue detail payload, with nested upcoming concerts."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique venue identifier")
    name: str = Field(..., description="Venue name")
    city: str = Field(..., description="City the venue is located in")
    country: str = Field(..., description="Country the venue is located in")
    capacity: Optional[int] = Field(None, description="Venue capacity")
    upcoming_concerts: List[VenueConcertRead] = Field(
        default_factory=list, description="Upcoming concerts scheduled at this venue"
    )


class VenueSearchQuery(BaseModel):
    """Query parameters accepted by `GET /api/v1/venues/search`."""

    q: Annotated[str, StringConstraints(strip_whitespace=True, min_length=MIN_SEARCH_QUERY_LENGTH)] = Field(
        ..., description="Search text to match against venue name/city/country"
    )


# Reuse the existing venue read schema as the item type for search results,
# rather than duplicating its shape.
VenueSearchResult = VenueResponse
