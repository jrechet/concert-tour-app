"""
Unit tests for stats Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import (
    CitiesResponse,
    VenuesResponse,
    CountryConcertCount,
    CountryConcertCountResponse,
    MonthlyConcertCount,
    MonthlyConcertCountResponse,
    PriceStatsResponse,
)


class TestCitiesResponse:
    """Test cases for CitiesResponse schema."""

    def test_valid_list_of_cities(self):
        response = CitiesResponse(cities=["London", "New York", "Paris"])
        assert response.cities == ["London", "New York", "Paris"]

    def test_empty_list_is_valid(self):
        response = CitiesResponse(cities=[])
        assert response.cities == []

    def test_missing_cities_raises(self):
        with pytest.raises(ValidationError):
            CitiesResponse()


class TestVenuesResponse:
    """Test cases for VenuesResponse schema."""

    def test_valid_list_of_venues(self):
        response = VenuesResponse(venues=["Madison Square Garden", "The O2 Arena"])
        assert response.venues == ["Madison Square Garden", "The O2 Arena"]

    def test_empty_list_is_valid(self):
        response = VenuesResponse(venues=[])
        assert response.venues == []

    def test_missing_venues_raises(self):
        with pytest.raises(ValidationError):
            VenuesResponse()


class TestCountryConcertCount:
    """Test cases for CountryConcertCount schema."""

    def test_valid_country_concert_count(self):
        item = CountryConcertCount(country="USA", concert_count=12)
        assert item.country == "USA"
        assert item.concert_count == 12

    def test_missing_country_raises(self):
        with pytest.raises(ValidationError):
            CountryConcertCount(concert_count=12)

    def test_missing_concert_count_raises(self):
        with pytest.raises(ValidationError):
            CountryConcertCount(country="USA")

    def test_invalid_concert_count_type_raises(self):
        with pytest.raises(ValidationError):
            CountryConcertCount(country="USA", concert_count="twelve")


class TestCountryConcertCountResponse:
    """Test cases for CountryConcertCountResponse schema."""

    def test_valid_list_of_country_counts(self):
        response = CountryConcertCountResponse(
            countries=[
                {"country": "USA", "concert_count": 12},
                {"country": "France", "concert_count": 5},
            ]
        )
        assert len(response.countries) == 2
        assert response.countries[0].country == "USA"
        assert response.countries[0].concert_count == 12

    def test_empty_list_is_valid(self):
        response = CountryConcertCountResponse(countries=[])
        assert response.countries == []

    def test_missing_countries_raises(self):
        with pytest.raises(ValidationError):
            CountryConcertCountResponse()

    def test_invalid_item_type_raises(self):
        with pytest.raises(ValidationError):
            CountryConcertCountResponse(
                countries=[{"country": "USA", "concert_count": "not-a-number"}]
            )


class TestMonthlyConcertCount:
    """Test cases for MonthlyConcertCount schema."""

    def test_valid_monthly_concert_count(self):
        item = MonthlyConcertCount(month="2026-01", count=7)
        assert item.month == "2026-01"
        assert item.count == 7

    def test_missing_month_raises(self):
        with pytest.raises(ValidationError):
            MonthlyConcertCount(count=7)

    def test_missing_count_raises(self):
        with pytest.raises(ValidationError):
            MonthlyConcertCount(month="2026-01")

    def test_invalid_count_type_raises(self):
        with pytest.raises(ValidationError):
            MonthlyConcertCount(month="2026-01", count="seven")


class TestMonthlyConcertCountResponse:
    """Test cases for MonthlyConcertCountResponse schema."""

    def test_valid_list_of_monthly_counts(self):
        response = MonthlyConcertCountResponse(
            months=[
                {"month": "2026-01", "count": 7},
                {"month": "2026-02", "count": 3},
            ]
        )
        assert len(response.months) == 2
        assert response.months[0].month == "2026-01"
        assert response.months[0].count == 7

    def test_empty_list_is_valid(self):
        response = MonthlyConcertCountResponse(months=[])
        assert response.months == []

    def test_missing_months_raises(self):
        with pytest.raises(ValidationError):
            MonthlyConcertCountResponse()

    def test_invalid_item_type_raises(self):
        with pytest.raises(ValidationError):
            MonthlyConcertCountResponse(
                months=[{"month": "2026-01", "count": "not-a-number"}]
            )


class TestPriceStatsResponse:
    """Test cases for PriceStatsResponse schema."""

    def test_valid_price_stats(self):
        response = PriceStatsResponse(lowest=45.0, average=87.5, highest=150.0)
        assert response.lowest == 45.0
        assert response.average == 87.5
        assert response.highest == 150.0

    def test_all_none_is_valid(self):
        response = PriceStatsResponse(lowest=None, average=None, highest=None)
        assert response.lowest is None
        assert response.average is None
        assert response.highest is None

    def test_missing_fields_raise(self):
        with pytest.raises(ValidationError):
            PriceStatsResponse(lowest=45.0, average=87.5)
