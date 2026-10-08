"""
Unit tests for the TicketPriceUpdate Pydantic schema.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.schemas.concert import TicketPriceUpdate


class TestTicketPriceUpdate:
    """Test cases for TicketPriceUpdate schema."""

    def test_valid_positive_price_accepted(self):
        update = TicketPriceUpdate(ticket_price="150.00")
        assert update.ticket_price == Decimal("150.00")

    def test_zero_price_accepted(self):
        update = TicketPriceUpdate(ticket_price="0")
        assert update.ticket_price == Decimal("0")

    def test_negative_price_raises(self):
        with pytest.raises(ValidationError):
            TicketPriceUpdate(ticket_price="-10.00")

    def test_non_numeric_price_raises(self):
        with pytest.raises(ValidationError):
            TicketPriceUpdate(ticket_price="not-a-number")

    def test_missing_price_raises(self):
        with pytest.raises(ValidationError):
            TicketPriceUpdate()
