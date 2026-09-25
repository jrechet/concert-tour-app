"""
Unit tests for stats Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import CitiesResponse, VenuesResponse


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
