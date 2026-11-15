"""
Unit tests for WeekdayStatsResponse Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import (
    CancellationStats,
    CapacityStats,
    MonthlyConcertCount,
    PRICE_STATS_DECIMALS,
    PriceStats,
    TourCancellationCount,
    WEEKDAY_NAMES,
    WeekdayCount,
    WeekdayStatsResponse,
)


class TestWeekdayCount:
    """Test cases for the `WeekdayCount` schema."""

    def test_zero_count_is_valid(self):
        item = WeekdayCount(weekday="Monday", count=0)
        assert item.count == 0

    def test_negative_count_raises(self):
        with pytest.raises(ValidationError):
            WeekdayCount(weekday="Monday", count=-1)


class TestWeekdayNames:
    """Test cases for the `WEEKDAY_NAMES` constant."""

    def test_has_seven_entries_monday_to_sunday(self):
        assert len(WEEKDAY_NAMES) == 7
        assert WEEKDAY_NAMES[0] == "Monday"
        assert WEEKDAY_NAMES[-1] == "Sunday"


class TestWeekdayStatsResponse:
    """Test cases for the `WeekdayStatsResponse` schema."""

    def test_valid_payload_serializes_and_preserves_order(self):
        weekdays = [WeekdayCount(weekday=name, count=index) for index, name in enumerate(WEEKDAY_NAMES)]
        response = WeekdayStatsResponse(weekdays=weekdays)
        dumped = response.model_dump()
        assert dumped == {
            "weekdays": [{"weekday": name, "count": index} for index, name in enumerate(WEEKDAY_NAMES)]
        }

    def test_out_of_order_weekdays_raises(self):
        weekdays = [WeekdayCount(weekday=name, count=0) for name in reversed(WEEKDAY_NAMES)]
        with pytest.raises(ValidationError):
            WeekdayStatsResponse(weekdays=weekdays)

    def test_wrong_number_of_weekdays_raises(self):
        weekdays = [WeekdayCount(weekday=name, count=0) for name in WEEKDAY_NAMES[:6]]
        with pytest.raises(ValidationError):
            WeekdayStatsResponse(weekdays=weekdays)


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


class TestCancellationStats:
    """Test cases for the `CancellationStats` and `TourCancellationCount` schemas."""

    def test_valid_payload_with_populated_by_tour(self):
        stats = CancellationStats(
            total_concerts=100,
            cancelled_concerts=5,
            cancellation_rate=5.0,
            by_tour=[
                TourCancellationCount(tour_id=1, tour_name="World Tour 2026", cancelled_concerts=5),
            ],
        )
        assert stats.model_dump() == {
            "total_concerts": 100,
            "cancelled_concerts": 5,
            "cancellation_rate": 5.0,
            "by_tour": [
                {"tour_id": 1, "tour_name": "World Tour 2026", "cancelled_concerts": 5},
            ],
        }

    def test_default_payload_is_all_zero_with_empty_by_tour(self):
        stats = CancellationStats(total_concerts=0, cancelled_concerts=0, cancellation_rate=0.0)
        assert stats.model_dump() == {
            "total_concerts": 0,
            "cancelled_concerts": 0,
            "cancellation_rate": 0.0,
            "by_tour": [],
        }

    def test_negative_total_concerts_raises(self):
        with pytest.raises(ValidationError):
            CancellationStats(total_concerts=-1, cancelled_concerts=0, cancellation_rate=0.0)

    def test_negative_cancelled_concerts_raises(self):
        with pytest.raises(ValidationError):
            CancellationStats(total_concerts=10, cancelled_concerts=-1, cancellation_rate=0.0)

    def test_cancellation_rate_above_100_raises(self):
        with pytest.raises(ValidationError):
            CancellationStats(total_concerts=10, cancelled_concerts=5, cancellation_rate=100.1)

    def test_cancelled_concerts_exceeding_total_raises(self):
        with pytest.raises(ValidationError):
            CancellationStats(total_concerts=5, cancelled_concerts=10, cancellation_rate=50.0)
