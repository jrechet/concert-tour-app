"""
Pydantic schemas for TicketTier entities.
"""

from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, ConfigDict, Field, field_validator

TICKET_TIER_PRICE_DECIMAL_PLACES = 2


class TicketTierRead(BaseModel):
    """Schema for reading a ticket tier, serialized from an ORM instance."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique ticket tier identifier")
    name: str = Field(..., description="Ticket tier name")
    price: Decimal = Field(..., description="Ticket tier price")

    @field_validator("price")
    @classmethod
    def quantize_price(cls, v: Decimal) -> Decimal:
        """Normalize to exactly 2 decimal places, matching the `Numeric(10, 2)` column."""
        return Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
