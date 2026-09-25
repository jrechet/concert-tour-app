"""
Unit tests for the TourSummary Pydantic schema.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.schemas.tour import TourSummary


class TestTourSummary:
    """Test cases for TourSummary schema."""

    def test_valid_summary_serializes_correctly(self):
        summary = TourSummary(
            tour_id=1,
            date_count=12,
            first_date=date(2024, 6, 1),
            last_date=date(2024, 12, 31),
            distinct_city_count=9,
        )

        data = summary.dict()
        assert data == {
            "tour_id": 1,
            "date_count": 12,
            "first_date": date(2024, 6, 1),
            "last_date": date(2024, 12, 31),
            "distinct_city_count": 9,
        }
        assert "2024-06-01" in summary.json()

    def test_null_dates_are_valid(self):
        summary = TourSummary(
            tour_id=2,
            date_count=0,
            first_date=None,
            last_date=None,
            distinct_city_count=0,
        )

        assert summary.first_date is None
        assert summary.last_date is None

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            TourSummary(date_count=1, distinct_city_count=1)
