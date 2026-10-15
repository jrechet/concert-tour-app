"""
Pydantic schemas for creating and returning LineupAct records.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

ARTIST_NAME_MAX_LENGTH = 200


class LineupActCreate(BaseModel):
    """Schema for adding a support act to a concert's lineup."""

    artist_name: str = Field(
        ..., min_length=1, max_length=ARTIST_NAME_MAX_LENGTH, description="Name of the performing act"
    )
    set_order: int = Field(..., ge=1, description="Running order position (1 plays first)")

    @field_validator("artist_name")
    @classmethod
    def strip_artist_name(cls, v: str) -> str:
        """Reject a name that is only whitespace, and trim surrounding
        whitespace from valid ones."""
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("artist_name must not be blank")
        return trimmed


class LineupActRead(BaseModel):
    """Schema for lineup act API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique lineup act identifier")
    concert_id: int = Field(..., description="ID of the concert this act belongs to")
    artist_name: str = Field(..., description="Name of the performing act")
    set_order: int = Field(..., description="Running order position (1 plays first)")
