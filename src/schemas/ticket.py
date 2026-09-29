"""
Pydantic schemas for ticket purchase requests.
"""

from pydantic import BaseModel, Field


class TicketPurchaseRequest(BaseModel):
    """Schema for the request body of the buy-tickets endpoint."""

    quantity: int = Field(..., gt=0, description="Number of tickets to purchase; must be at least 1")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "quantity": 2,
            }
        }
