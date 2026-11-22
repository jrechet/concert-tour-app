"""
Pydantic schemas for Artist entities.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ARTIST_NAME_MAX_LENGTH = 200


class ArtistSummary(BaseModel):
    """Schema for an artist listing entry."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Artist name")
    tour_count: int = Field(..., ge=0, description="Number of tours for this artist")


class ArtistDetail(BaseModel):
    """Read model for `GET /api/v1/artists/{id}`."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Artist id")
    name: str = Field(..., description="Artist name")
    concert_count: int = Field(..., ge=0, description="Number of non-cancelled concerts for this artist")


class ArtistUpdate(BaseModel):
    """Schema for the request body of a partial artist update.

    `name` is optional so a client may send an empty body, but when present
    it must not be blank: surrounding whitespace is stripped first, then a
    whitespace-only value is rejected so `"   "` is a 422, not a rename to
    an empty string. Unset vs. explicitly-empty is distinguished downstream
    by the caller using `model_dump(exclude_unset=True)`.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=ARTIST_NAME_MAX_LENGTH, description="Artist name")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        """Strip surrounding whitespace and reject a blank/whitespace-only value."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty or whitespace")
        return v
