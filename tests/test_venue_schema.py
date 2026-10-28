"""Unit tests for the `VenueRead` schema."""

import pytest
from pydantic import ValidationError

from src.models.venue import Venue
from src.schemas.venue import VenueRead


def create_venue(db_session, name="Madison Square Garden", city="New York", country="USA", capacity=20000):
    """Persist a real `Venue` row and return it."""
    venue = Venue(name=name, city=city, country=country, capacity=capacity)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return venue


class TestVenueRead:
    """Coverage for `VenueRead.model_validate`."""

    def test_serializes_persisted_venue_to_expected_fields(self, db_session):
        venue = create_venue(db_session, name="Wembley Stadium", city="London", country="UK", capacity=90000)

        read = VenueRead.model_validate(venue)
        dumped = read.model_dump()

        assert dumped == {
            "id": venue.id,
            "name": "Wembley Stadium",
            "city": "London",
            "country": "UK",
            "capacity": 90000,
        }

    def test_non_integer_capacity_string_is_rejected(self, db_session):
        venue = create_venue(db_session)

        with pytest.raises(ValidationError):
            VenueRead(id=venue.id, name=venue.name, city=venue.city, country=venue.country, capacity="not-a-number")

    def test_serialized_payload_has_no_unexpected_keys(self, db_session):
        venue = create_venue(db_session, name="Red Rocks", city="Morrison", country="USA", capacity=9525)

        read = VenueRead.model_validate(venue)

        assert set(read.model_dump().keys()) == {"id", "name", "city", "country", "capacity"}
