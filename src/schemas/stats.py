"""
Pydantic schemas for stats API responses.
"""

from typing import List
from pydantic import BaseModel, Field


class CitiesResponse(BaseModel):
    """Schema wrapping the distinct list of cities hosting at least one concert."""

    cities: List[str] = Field(..., description="Distinct, alphabetically sorted list of cities")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "cities": ["London", "New York", "Paris"]
            }
        }


class VenuesResponse(BaseModel):
    """Schema wrapping the distinct list of venue names hosting at least one concert."""

    venues: List[str] = Field(..., description="Distinct, alphabetically sorted list of venue names")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "venues": ["Madison Square Garden", "The O2 Arena"]
            }
        }
