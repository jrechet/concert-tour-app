"""
Pydantic schemas for stats API responses.
"""

from typing import List

from pydantic import BaseModel, Field


class CitiesResponse(BaseModel):
    """Schema for the distinct-cities stats response."""

    cities: List[str] = Field(
        ..., description="Sorted list of distinct cities hosting at least one concert"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "cities": ["Chicago", "New York", "San Francisco"],
            }
        }


class VenuesResponse(BaseModel):
    """Schema for the distinct-venues stats response."""

    venues: List[str] = Field(
        ..., description="Sorted list of distinct venue names hosting at least one concert"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "venues": ["Madison Square Garden", "The Fillmore"],
            }
        }
