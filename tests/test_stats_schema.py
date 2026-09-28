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
