"""
Unit tests for WeekdayStatsResponse Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import (
    CapacityStats,
    MonthlyConcertCount,
    PRICE_STATS_DECIMALS,
    PriceStats,
    WeekdayStatsResponse,
)


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


def test_capacity_stats_accepts_positive_values():
    stats = CapacityStats(total_capacity=1000, tickets_sold=250, seats_left=750)
    assert stats.total_capacity == 1000
    assert stats.tickets_sold == 250
    assert stats.seats_left == 750


def test_capacity_stats_accepts_zeros():
    stats = CapacityStats(total_capacity=0, tickets_sold=0, seats_left=0)
    assert stats.total_capacity == 0
    assert stats.tickets_sold == 0
    assert stats.seats_left == 0


@pytest.mark.parametrize("field", ["total_capacity", "tickets_sold", "seats_left"])
def test_capacity_stats_rejects_negative_values(field):
    payload = {"total_capacity": 1000, "tickets_sold": 250, "seats_left": 750}
    payload[field] = -1
    with pytest.raises(ValidationError):
        CapacityStats(**payload)


def test_capacity_stats_serializes_expected_keys():
    stats = CapacityStats(total_capacity=1000, tickets_sold=250, seats_left=750)
    dumped = stats.model_dump()
    assert set(dumped.keys()) == {"total_capacity", "tickets_sold", "seats_left"}


class TestMonthlyConcertCount:
    """Test cases for the `MonthlyConcertCount` schema's `month` pattern."""

    def test_valid_month_is_accepted(self):
        item = MonthlyConcertCount(month="2026-01", count=7)
        assert item.month == "2026-01"
        assert item.count == 7

    @pytest.mark.parametrize(
        "month",
        ["2026-13", "202-01", "2026-1", "2026/01", "2026-00", "not-a-month"],
    )
    def test_malformed_month_raises(self, month):
        with pytest.raises(ValidationError):
            MonthlyConcertCount(month=month, count=1)


class TestPriceStats:
    """Test cases for the `PriceStats` schema."""

    def test_all_values_populated_round_trips(self):
        stats = PriceStats(min=10.0, avg=20.0, max=30.0)
        assert stats.model_dump() == {"min": 10.0, "avg": 20.0, "max": 30.0}

    def test_defaults_to_all_null(self):
        stats = PriceStats()
        assert stats.model_dump() == {"min": None, "avg": None, "max": None}

    @pytest.mark.parametrize("field", ["min", "avg", "max"])
    def test_non_numeric_value_raises(self, field):
        payload = {"min": 10.0, "avg": 20.0, "max": 30.0}
        payload[field] = "not-a-number"
        with pytest.raises(ValidationError):
            PriceStats(**payload)

    def test_avg_is_rounded_to_configured_precision(self):
        stats = PriceStats(min=10.0, avg=20.12345, max=30.0)
        assert stats.avg == round(20.12345, PRICE_STATS_DECIMALS)
