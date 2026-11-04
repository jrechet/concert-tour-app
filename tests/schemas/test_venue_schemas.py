"""
Unit tests for the VenueDetailRead/VenueConcertRead Pydantic schemas.
"""

from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.schemas.venue import VenueConcertRead, VenueDetailRead


def make_concert(id=1, title="The Headliners Live", start_datetime=None, status="active"):
    """Build a Concert-ORM-like object matching `VenueConcertRead`'s shape."""
    return SimpleNamespace(
        id=id,
        title=title,
        start_datetime=start_datetime or datetime(2024, 7, 15, 20, 0, 0),
        status=status,
    )


def make_venue(id=1, name="Madison Square Garden", city="New York", country="USA", capacity=20000, upcoming_concerts=None):
    """Build a Venue-ORM-like object with an `upcoming_concerts` attribute."""
    return SimpleNamespace(
        id=id,
        name=name,
        city=city,
        country=country,
        capacity=capacity,
        upcoming_concerts=upcoming_concerts if upcoming_concerts is not None else [],
    )


class TestVenueDetailRead:
    """Test cases for the `VenueDetailRead` schema."""

    def test_venue_detail_from_orm_object_maps_all_venue_fields(self):
        venue = make_venue(id=3, name="Wembley Stadium", city="London", country="UK", capacity=90000)

        detail = VenueDetailRead.model_validate(venue)

        assert detail.id == 3
        assert detail.name == "Wembley Stadium"
        assert detail.city == "London"
        assert detail.country == "UK"
        assert detail.capacity == 90000
        assert detail.upcoming_concerts == []

    def test_venue_detail_validates_from_plain_dict(self):
        payload = {
            "id": 1,
            "name": "Arena",
            "city": "Paris",
            "country": "France",
            "capacity": 5000,
            "upcoming_concerts": [],
        }

        detail = VenueDetailRead(**payload)

        assert detail.name == "Arena"
        assert detail.city == "Paris"
        assert detail.country == "France"
        assert detail.capacity == 5000

    def test_venue_detail_nests_concerts_in_given_order(self):
        concerts = [
            make_concert(id=1, title="First Night", start_datetime=datetime(2024, 7, 15, 20, 0, 0), status="active"),
            make_concert(id=2, title="Second Night", start_datetime=datetime(2024, 8, 1, 19, 30, 0), status="planned"),
        ]
        venue = make_venue(upcoming_concerts=concerts)

        detail = VenueDetailRead.model_validate(venue)

        assert [concert.id for concert in detail.upcoming_concerts] == [1, 2]
        assert detail.upcoming_concerts[0].title == "First Night"
        assert detail.upcoming_concerts[1].title == "Second Night"

    def test_venue_detail_upcoming_concerts_defaults_to_empty_list(self):
        detail = VenueDetailRead(id=1, name="Arena", city="Paris", country="France", capacity=None)

        assert detail.upcoming_concerts == []


class TestVenueConcertRead:
    """Test cases for the `VenueConcertRead` schema."""

    def test_venue_concert_read_from_orm_object(self):
        concert = make_concert(id=7, title="The Headliners Live", status="active")

        read = VenueConcertRead.model_validate(concert)

        assert read.id == 7
        assert read.title == "The Headliners Live"
        assert read.start_datetime == datetime(2024, 7, 15, 20, 0, 0)
        assert read.status == "active"

    def test_venue_concert_read_rejects_missing_start_datetime(self):
        with pytest.raises(ValidationError):
            VenueConcertRead(id=1, title="The Headliners Live", status="active")
