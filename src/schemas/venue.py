"""Venue Pydantic schemas for API requests and responses."""

from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime


class VenueBase(BaseModel):
    """Base venue schema with common fields."""
    
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    capacity: int
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    
    @field_validator('capacity')
    @classmethod
    def validate_capacity(cls, v):
        """Validate venue capacity is positive."""
        if v <= 0:
            raise ValueError('Venue capacity must be positive')
        return v
    
    @field_validator('zip_code')
    @classmethod
    def validate_zip_code(cls, v):
        """Validate zip code format."""
        if not v.replace('-', '').isdigit():
            raise ValueError('Zip code must contain only digits and hyphens')
        return v


class VenueCreate(VenueBase):
    """Schema for creating a new venue."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Madison Square Garden",
                "address": "4 Pennsylvania Plaza",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "capacity": 20000,
                "phone_number": "+1-212-465-6741",
                "email": "info@msg.com",
                "website": "https://www.msg.com"
            }
        }
    )


class VenueUpdate(BaseModel):
    """Schema for updating an existing venue."""
    
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    capacity: Optional[int] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    
    @field_validator('capacity')
    @classmethod
    def validate_capacity(cls, v):
        """Validate venue capacity is positive."""
        if v is not None and v <= 0:
            raise ValueError('Venue capacity must be positive')
        return v
    
    @field_validator('zip_code')
    @classmethod
    def validate_zip_code(cls, v):
        """Validate zip code format."""
        if v is not None and not v.replace('-', '').isdigit():
            raise ValueError('Zip code must contain only digits and hyphens')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Venue Name",
                "capacity": 25000,
                "email": "updated@venue.com"
            }
        }
    )


class VenueResponse(VenueBase):
    """Schema for venue API responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VenueListResponse(BaseModel):
    """Schema for paginated venue list responses."""
    
    venues: list[VenueResponse]
    total: int
    page: int
    per_page: int
    pages: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "venues": [
                    {
                        "id": 1,
                        "name": "Madison Square Garden",
                        "address": "4 Pennsylvania Plaza",
                        "city": "New York",
                        "state": "NY",
                        "zip_code": "10001",
                        "capacity": 20000,
                        "phone_number": "+1-212-465-6741",
                        "email": "info@msg.com",
                        "website": "https://www.msg.com",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00"
                    }
                ],
                "total": 100,
                "page": 1,
                "per_page": 10,
                "pages": 10
            }
        }
    )
