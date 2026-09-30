"""
Unit tests for WeekdayStatsResponse Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import WeekdayStatsResponse


WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class TestWeekdayStatsResponse:
    """Test cases for WeekdayStatsResponse schema."""

    def test_valid_payload_round_trips(self):
        payload = {
            "monday": 1,
            "tuesday": 2,
            "wednesday": 3,
            "thursday": 4,
            "friday": 5,
            "saturday": 6,
            "sunday": 0,
        }
        response = WeekdayStatsResponse(**payload)
        assert response.model_dump() == payload

    @pytest.mark.parametrize("weekday", WEEKDAYS)
    def test_negative_value_raises(self, weekday):
        payload = {day: 1 for day in WEEKDAYS}
        payload[weekday] = -1
        with pytest.raises(ValidationError):
            WeekdayStatsResponse(**payload)

    @pytest.mark.parametrize("weekday", WEEKDAYS)
    def test_missing_field_raises(self, weekday):
        payload = {day: 1 for day in WEEKDAYS}
        del payload[weekday]
        with pytest.raises(ValidationError):
            WeekdayStatsResponse(**payload)

    def test_field_order_is_monday_to_sunday(self):
        assert list(WeekdayStatsResponse.model_fields.keys()) == WEEKDAYS
