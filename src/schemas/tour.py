"""
Pydantic schemas for Tour entities.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, validator


class TourCreate(BaseModel):
    """Schema for creating a new tour."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Tour name")
    artist: str = Field(..., min_length=1, max_length=100, description="Artist name")
    start_date: date = Field(..., description="Tour start date")
    end_date: date = Field(..., description="Tour end date")
    description: Optional[str] = Field(None, max_length=1000, description="Tour description")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Ensure end_date is not before start_date."""
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after or equal to start_date')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "World Tour 2024",
                "artist": "The Beatles",
                "start_date": "2024-06-01",
                "end_date": "2024-12-31",
                "description": "An amazing world tour featuring classic hits"
            }
        }


class TourUpdate(BaseModel):
    """Schema for updating an existing tour."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Tour name")
    artist: Optional[str] = Field(None, min_length=1, max_length=100, description="Artist name")
    start_date: Optional[date] = Field(None, description="Tour start date")
    end_date: Optional[date] = Field(None, description="Tour end date")
    description: Optional[str] = Field(None, max_length=1000, description="Tour description")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Ensure end_date is not before start_date if both are provided."""
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError('end_date must be after or equal to start_date')
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "Updated World Tour 2024",
                "description": "Updated description for the tour"
            }
        }


class TourResponse(BaseModel):
    """Schema for tour API responses."""
    
    id: int = Field(..., description="Unique tour identifier")
    name: str = Field(..., description="Tour name")
    artist: str = Field(..., description="Artist name")
    start_date: date = Field(..., description="Tour start date")
    end_date: date = Field(..., description="Tour end date")
    description: Optional[str] = Field(None, description="Tour description")
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "World Tour 2024",
                "artist": "The Beatles",
                "start_date": "2024-06-01",
                "end_date": "2024-12-31",
                "description": "An amazing world tour featuring classic hits"
            }
        }
