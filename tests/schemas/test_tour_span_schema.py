"""
Unit tests for the TourSpanRead Pydantic schema.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.schemas.tour import TourSpanRead


class TestTourSpanRead:
    """Test cases for TourSpanRead schema."""

    def test_fully_populated_payload_validates(self):
        span = TourSpanRead(
            first_concert_date=date(2024, 6, 1),
            last_concert_date=date(2024, 12, 31),
            duration_days=213,
        )
        assert span.first_concert_date == date(2024, 6, 1)
        assert span.last_concert_date == date(2024, 12, 31)
        assert span.duration_days == 213

    def test_all_null_payload_validates(self):
        span = TourSpanRead(
            first_concert_date=None,
            last_concert_date=None,
            duration_days=None,
        )
        assert span.first_concert_date is None
        assert span.last_concert_date is None
        assert span.duration_days is None

    def test_non_date_first_concert_date_raises(self):
        with pytest.raises(ValidationError):
            TourSpanRead(
                first_concert_date="not-a-date",
                last_concert_date=None,
                duration_days=None,
            )

    def test_non_int_duration_days_raises(self):
        with pytest.raises(ValidationError):
            TourSpanRead(
                first_concert_date=None,
                last_concert_date=None,
                duration_days="abc",
            )
