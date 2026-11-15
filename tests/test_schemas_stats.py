"""
Unit tests for the YearStats Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import YearStats


class TestYearStats:
    """Test cases for YearStats schema."""

    def test_valid_payload(self):
        stats = YearStats(year=2026, concerts=42, cancelled=3, tickets_sold=15000)
        assert stats.year == 2026
        assert stats.concerts == 42
        assert stats.cancelled == 3
        assert stats.tickets_sold == 15000

    def test_valid_payload_serializes_to_exactly_four_keys(self):
        stats = YearStats(year=2026, concerts=42, cancelled=3, tickets_sold=15000)
        assert stats.model_dump() == {
            "year": 2026,
            "concerts": 42,
            "cancelled": 3,
            "tickets_sold": 15000,
        }

    def test_negative_concerts_raises(self):
        with pytest.raises(ValidationError):
            YearStats(year=2026, concerts=-1, cancelled=0, tickets_sold=0)

    def test_negative_cancelled_raises(self):
        with pytest.raises(ValidationError):
            YearStats(year=2026, concerts=10, cancelled=-1, tickets_sold=0)

    def test_negative_tickets_sold_raises(self):
        with pytest.raises(ValidationError):
            YearStats(year=2026, concerts=10, cancelled=0, tickets_sold=-1)

    def test_cancelled_exceeding_concerts_raises(self):
        with pytest.raises(ValidationError):
            YearStats(year=2026, concerts=5, cancelled=6, tickets_sold=0)

    def test_cancelled_equal_to_concerts_is_valid(self):
        stats = YearStats(year=2026, concerts=5, cancelled=5, tickets_sold=0)
        assert stats.cancelled == stats.concerts == 5
