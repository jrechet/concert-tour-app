"""
Unit tests for the `VenueCreate` and `VenueRead` Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.models import Venue
from src.schemas.venue import VenueCreate, VenueRead


class TestVenueCreate:
    """Test cases for the `VenueCreate` schema."""

    def test_valid_payload_validates_and_exposes_parsed_values(self):
        venue = VenueCreate(name="Madison Square Garden", city="New York", country="USA", capacity=20000)

        assert venue.name == "Madison Square Garden"
        assert venue.city == "New York"
        assert venue.country == "USA"
        assert venue.capacity == 20000

    def test_capacity_zero_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(name="Arena", city="Paris", country="France", capacity=0)

    def test_capacity_negative_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(name="Arena", city="Paris", country="France", capacity=-5)

    def test_missing_name_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(city="Paris", country="France", capacity=5000)

    def test_empty_name_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(name="", city="Paris", country="France", capacity=5000)

    def test_whitespace_only_name_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(name="   ", city="Paris", country="France", capacity=5000)

    def test_missing_city_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(name="Arena", country="France", capacity=5000)

    def test_missing_country_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(name="Arena", city="Paris", capacity=5000)

    def test_missing_capacity_fails(self):
        with pytest.raises(ValidationError):
            VenueCreate(name="Arena", city="Paris", country="France")


class TestVenueRead:
    """Test cases for the `VenueRead` schema."""

    def test_serializes_persisted_venue_orm_instance(self, db_session):
        venue = Venue(name="Wembley Stadium", city="London", country="UK", capacity=90000)
        db_session.add(venue)
        db_session.commit()
        db_session.refresh(venue)

        read = VenueRead.model_validate(venue)

        assert read.id == venue.id
        assert read.name == "Wembley Stadium"
        assert read.city == "London"
        assert read.country == "UK"
        assert read.capacity == 90000
