from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VenueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., max_length=500)
    capacity: int = Field(..., ge=1)


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    capacity: Optional[int] = Field(None, ge=1)


class VenueResponse(BaseModel):
    id: int
    name: str
    city: str
    address: str
    capacity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VenueListParams(BaseModel):
    search: Optional[str] = Field(None, description="Search in venue name or city")
    city: Optional[str] = Field(None, description="Filter by city")
    min_capacity: Optional[int] = Field(None, ge=1, description="Minimum capacity filter")
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class VenueListResponse(BaseModel):
    venues: list[VenueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
