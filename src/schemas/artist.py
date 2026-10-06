"""
Pydantic schemas for Artist entities.
"""

from pydantic import BaseModel, Field


class ArtistSummary(BaseModel):
    """Schema for an artist listing entry."""

    name: str = Field(..., description="Artist name")
    tour_count: int = Field(..., ge=1, description="Number of tours for this artist")
