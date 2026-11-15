"""Unit tests for the `VenueUpdate` schema."""

import pytest
from pydantic import ValidationError

from src.schemas.venue import VenueUpdate


class TestVenueUpdate:
    """Test cases for the `VenueUpdate` partial-update schema."""

    def test_only_name_is_accepted(self):
        update = VenueUpdate(name="Madison Square Garden")

        assert update.name == "Madison Square Garden"
        assert update.city is None
        assert update.country is None
        assert update.capacity is None

    def test_only_city_is_accepted(self):
        update = VenueUpdate(city="New York")

        assert update.city == "New York"
        assert update.name is None
        assert update.country is None
        assert update.capacity is None

    def test_only_country_is_accepted(self):
        update = VenueUpdate(country="USA")

        assert update.country == "USA"
        assert update.name is None
        assert update.city is None
        assert update.capacity is None

    def test_only_capacity_is_accepted(self):
        update = VenueUpdate(capacity=20000)

        assert update.capacity == 20000
        assert update.name is None
        assert update.city is None
        assert update.country is None

    def test_any_combination_of_fields_is_accepted(self):
        update = VenueUpdate(name="Arena", city="Paris")

        assert update.name == "Arena"
        assert update.city == "Paris"
        assert update.country is None
        assert update.capacity is None

    def test_all_fields_together_is_accepted(self):
        update = VenueUpdate(name="Arena", city="Paris", country="France", capacity=5000)

        assert update.name == "Arena"
        assert update.city == "Paris"
        assert update.country == "France"
        assert update.capacity == 5000

    def test_capacity_zero_fails(self):
        with pytest.raises(ValidationError):
            VenueUpdate(capacity=0)

    def test_capacity_negative_fails(self):
        with pytest.raises(ValidationError):
            VenueUpdate(capacity=-5)

    def test_empty_name_fails(self):
        with pytest.raises(ValidationError):
            VenueUpdate(name="")

    def test_whitespace_only_name_fails(self):
        with pytest.raises(ValidationError):
            VenueUpdate(name="   ")

    def test_entirely_empty_body_fails(self):
        with pytest.raises(ValidationError):
            VenueUpdate()

    def test_entirely_null_body_fails(self):
        with pytest.raises(ValidationError):
            VenueUpdate(name=None, city=None, country=None, capacity=None)
