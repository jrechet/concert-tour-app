"""
Unit tests for the ConcertPriceUpdate Pydantic schema.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.schemas.concert import ConcertPriceUpdate


class TestConcertPriceUpdate:
    """Test cases for ConcertPriceUpdate schema."""

    def test_price_update_accepts_decimal_string(self):
        update = ConcertPriceUpdate(ticket_price="49.50")
        assert update.ticket_price == Decimal("49.50")

    def test_price_update_rejects_negative_price(self):
        with pytest.raises(ValidationError):
            ConcertPriceUpdate(ticket_price="-1.00")

    def test_price_update_rejects_missing_ticket_price(self):
        with pytest.raises(ValidationError):
            ConcertPriceUpdate()

    def test_price_update_rejects_non_numeric_ticket_price(self):
        with pytest.raises(ValidationError):
            ConcertPriceUpdate(ticket_price="not-a-number")
