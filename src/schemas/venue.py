"""
Pydantic schemas for Venue entities.
"""

from typing import Optional
from pydantic import BaseModel, Field


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
