"""
Pydantic schema for concert occupancy responses.
"""

from typing import Optional

from pydantic import BaseModel, Field


class OccupancyResponse(BaseModel):
    """Ticket sales relative to venue capacity for a single concert.

    `capacity` and `percentage_sold` are null when the concert's venue has
    no capacity set, since a percentage can't be computed without it.
    """

    concert_id: int = Field(..., description="Unique concert identifier")
    tickets_sold: int = Field(..., description="Number of tickets sold for this concert")
    capacity: Optional[int] = Field(None, description="Venue capacity; null when unknown")
    percentage_sold: Optional[float] = Field(
        None,
        description="Tickets sold as a percentage of capacity, rounded to 1 decimal place; null when capacity is unknown",
    )

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "concert_id": 1,
                "tickets_sold": 15000,
                "capacity": 20000,
                "percentage_sold": 75.0,
            }
        }
