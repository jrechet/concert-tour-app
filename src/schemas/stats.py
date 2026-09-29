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


class CountResponse(BaseModel):
    """Schema wrapping the total number of concerts."""

    count: int = Field(..., description="Total number of concerts")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "count": 42
            }
        }


class UpcomingCountResponse(BaseModel):
    """Schema wrapping the count of concerts scheduled today or later."""

    count: int = Field(..., description="Number of concerts scheduled today or later")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "count": 5
            }
        }


class CountryConcertCount(BaseModel):
    """Number of concerts hosted by a single country."""

    country: str = Field(..., description="Country name")
    concert_count: int = Field(..., description="Number of concerts hosted in this country")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "country": "USA",
                "concert_count": 12
            }
        }


class CountryConcertCountResponse(BaseModel):
    """Schema wrapping the per-country concert counts."""

    countries: List[CountryConcertCount] = Field(
        ..., description="Number of concerts per country"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "countries": [
                    {"country": "USA", "concert_count": 12},
                    {"country": "France", "concert_count": 5},
                ]
            }
        }


class MonthlyConcertCount(BaseModel):
    """Number of concerts hosted during a single calendar month."""

    month: str = Field(..., description="Calendar month in 'YYYY-MM' format")
    count: int = Field(..., description="Number of concerts in this month")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "month": "2026-01",
                "count": 7
            }
        }


class MonthlyConcertCountResponse(BaseModel):
    """Schema wrapping the per-month concert counts."""

    months: List[MonthlyConcertCount] = Field(
        ..., description="Number of concerts per calendar month"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "months": [
                    {"month": "2026-01", "count": 7},
                    {"month": "2026-02", "count": 3},
                ]
            }
        }
