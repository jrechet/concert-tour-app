"""
Pydantic schemas for LineupEntry entities.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LineupEntryResponse(BaseModel):
    """Schema for lineup entry API responses."""

    id: int = Field(..., description="Unique lineup entry identifier")
    artist_name: str = Field(..., description="Name of the supporting act")
    set_order: int = Field(..., description="Running order position (lower plays earlier)")
    set_time: Optional[datetime] = Field(None, description="Scheduled stage time, if known")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "artist_name": "The Openers",
                "set_order": 1,
                "set_time": "2024-07-15T19:00:00"
            }
        }
