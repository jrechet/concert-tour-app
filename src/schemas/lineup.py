"""
Pydantic schemas for creating and returning LineupEntry records.
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator


class LineupEntryCreate(BaseModel):
    """Schema for adding a lineup entry to a concert."""

    artist_name: str = Field(..., min_length=1, max_length=200, description="Name of the performing act")
    set_order: int = Field(..., ge=1, description="Running order position (1 plays first)")

    @validator("artist_name")
    def validate_artist_name_not_blank(cls, v):
        """Reject a name that is only whitespace, and trim surrounding
        whitespace from valid ones."""
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("artist_name must not be blank")
        return trimmed

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "artist_name": "The Openers",
                "set_order": 1,
            }
        }


class LineupReorderRequest(BaseModel):
    """Schema for moving a lineup entry to a new running-order position."""

    set_order: int = Field(..., ge=1, description="New running order position (1 plays first)")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "set_order": 2,
            }
        }


class LineupEntryOut(BaseModel):
    """Schema for lineup entry API responses."""

    id: int = Field(..., description="Unique lineup entry identifier")
    concert_id: int = Field(..., description="ID of the concert this entry belongs to")
    artist_name: str = Field(..., description="Name of the performing act")
    set_order: int = Field(..., description="Running order position (1 plays first)")
    created_at: datetime = Field(..., description="When this lineup entry was created")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "concert_id": 1,
                "artist_name": "The Openers",
                "set_order": 1,
                "created_at": "2026-09-29T00:00:00",
            }
        }
