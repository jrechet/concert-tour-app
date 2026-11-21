"""
Pydantic schemas for Artist entities.
"""

from pydantic import BaseModel, ConfigDict, Field


class ArtistSummary(BaseModel):
    """Schema for an artist listing entry."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Artist name")
    tour_count: int = Field(..., ge=0, description="Number of tours for this artist")


class ArtistDetail(BaseModel):
    """Read model for `GET /api/v1/artists/{id}`."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Artist id")
    name: str = Field(..., description="Artist name")
    concert_count: int = Field(..., ge=0, description="Number of non-cancelled concerts for this artist")
