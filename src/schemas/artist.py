"""
Pydantic schemas for Artist entities.
"""

from pydantic import BaseModel, ConfigDict, Field


class ArtistSummary(BaseModel):
    """Schema for an artist listing entry."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Artist name")
    tour_count: int = Field(..., ge=0, description="Number of tours for this artist")
