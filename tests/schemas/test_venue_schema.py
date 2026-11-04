"""
Unit tests for VenueConcertRead and VenueDetailRead Pydantic schemas.
"""

from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.schemas.venue import (
    VenueConcertRead,
    VenueCreate,
    VenueDetailRead,
    VenueListParams,
    VenueResponse,
)


def make_concert(id=1, title="The Headliners Live", date_time=None, status="active"):
    """Build a Concert-ORM-like object with a nested `tour` relationship,
    matching the real `Concert`/`Tour` models (`date_time`, `tour.name`,
    `tour.status`) rather than `VenueConcertRead`'s own field names."""
    tour = SimpleNamespace(name=title, status=status)
    return SimpleNamespace(
        id=id,
        date_time=date_time or datetime(2024, 7, 15, 20, 0, 0),
        tour=tour,
    )


def make_venue(
    id=1,
    name="Madison Square Garden",
    city="New York",
    country="USA",
    capacity=20000,
    upcoming_concerts=None,
):
    """Build a Venue-ORM-like object with an `upcoming_concerts` attribute."""
    return SimpleNamespace(
        id=id,
        name=name,
        city=city,
        country=country,
        capacity=capacity,
        upcoming_concerts=upcoming_concerts if upcoming_concerts is not None else [],
    )


class TestVenueConcertRead:
    """Test cases for the `VenueConcertRead` schema."""

    def test_serializes_concert_orm_object(self):
        concert = make_concert(id=7, title="The Headliners Live", status="active")

        read = VenueConcertRead.model_validate(concert)

        assert read.id == 7
        assert read.title == "The Headliners Live"
        assert read.start_datetime == datetime(2024, 7, 15, 20, 0, 0)
        assert read.status == "active"

    def test_accepts_plain_dict(self):
        payload = {
            "id": 1,
            "title": "The Headliners Live",
            "start_datetime": "2024-07-15T20:00:00",
            "status": "active",
        }

        read = VenueConcertRead(**payload)

        assert read.id == 1
        assert read.status == "active"

    def test_venue_concert_read_rejects_missing_start_datetime(self):
        with pytest.raises(ValidationError):
            VenueConcertRead(id=1, title="The Headliners Live", status="active")


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
            make_concert(id=1, title="First Night", date_time=datetime(2024, 7, 15, 20, 0, 0), status="active"),
            make_concert(id=2, title="Second Night", date_time=datetime(2024, 8, 1, 19, 30, 0), status="planned"),
        ]
        venue = make_venue(upcoming_concerts=concerts)

        detail = VenueDetailRead.model_validate(venue)

        assert [concert.id for concert in detail.upcoming_concerts] == [1, 2]
        assert detail.upcoming_concerts[0].title == "First Night"
        assert detail.upcoming_concerts[0].start_datetime == datetime(2024, 7, 15, 20, 0, 0)
        assert detail.upcoming_concerts[1].title == "Second Night"
        assert detail.upcoming_concerts[1].status == "planned"

    def test_venue_detail_upcoming_concerts_defaults_to_empty_list(self):
        detail = VenueDetailRead(id=1, name="Arena", city="Paris", country="France", capacity=None)

        assert detail.upcoming_concerts == []


class TestVenueCreate:
    """Test cases for VenueCreate schema."""

    def test_valid_payload_passes(self):
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


class TestVenueResponse:
    """Test cases for VenueResponse schema."""

    def test_serializes_venue_orm_instance(self):
        venue = make_venue(id=3, name="Wembley Stadium", city="London", country="UK", capacity=90000)

        response = VenueResponse.model_validate(venue)

        assert response.model_dump() == {
            "id": 3,
            "name": "Wembley Stadium",
            "city": "London",
            "country": "UK",
            "capacity": 90000,
        }

    def test_negative_capacity_fails(self):
        with pytest.raises(ValidationError):
            VenueResponse(id=1, name="Arena", city="Paris", country="France", capacity=-1)


class TestVenueListParams:
    """Test cases for VenueListParams schema."""

    def test_min_capacity_omitted_is_none(self):
        params = VenueListParams()
        assert params.min_capacity is None

    def test_min_capacity_zero_passes(self):
        params = VenueListParams(min_capacity=0)
        assert params.min_capacity == 0

    def test_min_capacity_positive_passes(self):
        params = VenueListParams(min_capacity=5000)
        assert params.min_capacity == 5000

    def test_min_capacity_negative_fails(self):
        with pytest.raises(ValidationError):
            VenueListParams(min_capacity=-1)
