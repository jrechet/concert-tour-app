"""
Unit tests for the `VenueCreate`, `VenueRead`, and `VenueDeleteConflict`
Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.models import Venue
from src.schemas.venue import VenueCreate, VenueDeleteConflict, VenueRead


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


class TestVenueDeleteConflict:
    """Test cases for the `VenueDeleteConflict` schema."""

    def test_valid_payload_validates_and_exposes_parsed_values(self):
        conflict = VenueDeleteConflict(
            detail="Venue cannot be deleted because it still hosts concerts",
            concert_count=3,
        )

        assert conflict.detail == "Venue cannot be deleted because it still hosts concerts"
        assert conflict.concert_count == 3

    def test_serializes_with_expected_field_names(self):
        conflict = VenueDeleteConflict(detail="Venue still hosts concerts", concert_count=3)

        assert conflict.model_dump() == {
            "detail": "Venue still hosts concerts",
            "concert_count": 3,
        }

    def test_missing_concert_count_fails(self):
        with pytest.raises(ValidationError):
            VenueDeleteConflict(detail="Venue still hosts concerts")

    def test_missing_detail_fails(self):
        with pytest.raises(ValidationError):
            VenueDeleteConflict(concert_count=3)

    def test_non_integer_concert_count_fails(self):
        with pytest.raises(ValidationError):
            VenueDeleteConflict(detail="Venue still hosts concerts", concert_count="three")

    def test_negative_concert_count_fails(self):
        with pytest.raises(ValidationError):
            VenueDeleteConflict(detail="Venue still hosts concerts", concert_count=-1)
