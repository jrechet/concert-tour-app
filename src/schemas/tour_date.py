"""Pydantic schemas for the tour dates listing API."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TourDateSort(str, Enum):
    """Allowed values for the `sort` query parameter on `GET /api/v1/tour-dates`.

    Any other value is rejected by FastAPI with a 422 before the route
    handler runs, since the parameter is typed as this enum.
    """

    NEXT_FIRST = "next_first"
    DATE_DESC = "date_desc"


class TourDateResponse(BaseModel):
    """Schema for a single entry in the tour dates listing.

    Mirrors the underlying `Concert` row (a tour date). `date_time` is
    always serialized as ISO-8601 UTC, regardless of the naive (assumed
    UTC) value stored in the database, so clients never have to guess the
    timezone of a bare timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique concert identifier")
    tour_id: int = Field(..., description="ID of the tour this concert belongs to")
    venue_id: int = Field(..., description="ID of the venue hosting this concert")
    date_time: datetime = Field(..., description="Concert date and time, in ISO-8601 UTC")

    @field_serializer("date_time")
    def serialize_date_time_as_utc(self, value: datetime) -> str:
        """Render `date_time` as ISO-8601 UTC, treating a naive value as
        already being UTC rather than the local timezone."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
