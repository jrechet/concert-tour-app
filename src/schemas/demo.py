"""
Pydantic schemas for the aggregated demo tour-overview endpoint.

These are built explicitly in `src.routers.demo` rather than returned
straight from the ORM (unlike most other response schemas here), since a
`Concert` row has no `ticket_tiers` relationship to read from directly.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class DemoTicketTierOut(BaseModel):
    """A priced ticket tier offered for a demo concert."""

    name: str = Field(..., description="Ticket tier name")
    price: Decimal = Field(..., description="Ticket tier price, as stored")

    class Config:
        """Pydantic configuration."""
        orm_mode = True


class DemoConcertOut(BaseModel):
    """A single tour stop in the demo tour overview."""

    id: int = Field(..., description="Unique concert identifier")
    venue_name: str = Field(..., description="Name of the venue hosting this concert")
    city: str = Field(..., description="City the venue is located in")
    date_time: datetime = Field(..., description="Concert date and time")
    status: str = Field(..., description="'past' or 'upcoming', relative to now")
    ticket_tiers: List[DemoTicketTierOut] = Field(
        default_factory=list, description="Priced ticket tiers offered for this concert"
    )

    class Config:
        """Pydantic configuration."""
        orm_mode = True


class DemoTourOverviewResponse(BaseModel):
    """Aggregated "what does my tour look like" view of the seeded demo tour."""

    tour_name: str = Field(..., description="Name of the demo tour")
    artist: str = Field(..., description="Name of the band/artist touring")
    status: Optional[str] = Field(None, description="Tour status")
    concert_count: int = Field(..., description="Number of concerts included in this response")
    past_concert_count: int = Field(..., description="Number of included concerts already in the past")
    upcoming_concert_count: int = Field(..., description="Number of included concerts today or in the future")
    concerts: List[DemoConcertOut] = Field(
        default_factory=list, description="Concerts on the tour, in date order"
    )

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "tour_name": "Neon Skyline Tour",
                "artist": "Aurora Belle",
                "status": "active",
                "concert_count": 3,
                "past_concert_count": 1,
                "upcoming_concert_count": 2,
                "concerts": [
                    {
                        "id": 1,
                        "venue_name": "Madison Square Garden",
                        "city": "New York",
                        "date_time": "2026-09-12T17:28:44",
                        "status": "past",
                        "ticket_tiers": [
                            {"name": "General Admission", "price": "75.00"},
                            {"name": "VIP", "price": "150.00"},
                            {"name": "Premium", "price": "300.00"},
                        ],
                    }
                ],
            }
        }
