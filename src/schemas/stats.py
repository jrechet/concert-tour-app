"""
Pydantic schemas for stats API responses.
"""

from typing import List, Optional

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


class PriceStatsResponse(BaseModel):
    """Schema wrapping ticket price statistics over upcoming, non-cancelled
    concerts with a known price.

    All three fields are `None` when there are no eligible concerts, rather
    than 0, since 0 would misleadingly imply a real price of zero.
    """

    lowest: Optional[float] = Field(..., description="Lowest ticket price, or null if no eligible concerts")
    average: Optional[float] = Field(..., description="Average ticket price, or null if no eligible concerts")
    highest: Optional[float] = Field(..., description="Highest ticket price, or null if no eligible concerts")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "lowest": 45.0,
                "average": 87.5,
                "highest": 150.0,
            }
        }


class WeekdayStatsResponse(BaseModel):
    """Schema wrapping the number of concerts held on each day of the week."""

    monday: int = Field(..., ge=0, description="Number of concerts held on Mondays")
    tuesday: int = Field(..., ge=0, description="Number of concerts held on Tuesdays")
    wednesday: int = Field(..., ge=0, description="Number of concerts held on Wednesdays")
    thursday: int = Field(..., ge=0, description="Number of concerts held on Thursdays")
    friday: int = Field(..., ge=0, description="Number of concerts held on Fridays")
    saturday: int = Field(..., ge=0, description="Number of concerts held on Saturdays")
    sunday: int = Field(..., ge=0, description="Number of concerts held on Sundays")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "monday": 3,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 4,
                "friday": 6,
                "saturday": 8,
                "sunday": 5,
            }
        }
