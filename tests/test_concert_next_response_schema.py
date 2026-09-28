"""Unit tests for the `ConcertNextResponse` schema and its nested venue/city info."""

from datetime import datetime

from src.schemas.concert import ConcertNextResponse, NextConcertCity, NextConcertVenue


class TestConcertNextResponse:
    """Coverage for `ConcertNextResponse` nesting venue and city data."""

    def test_builds_from_nested_venue_and_city(self):
        response = ConcertNextResponse(
            id=1,
            date_time=datetime(2024, 7, 15, 20, 0, 0),
            is_cancelled=False,
            venue=NextConcertVenue(name="Madison Square Garden", capacity=20000),
            city=NextConcertCity(name="New York", country="USA"),
        )

        assert response.id == 1
        assert response.venue.name == "Madison Square Garden"
        assert response.venue.capacity == 20000
        assert response.city.name == "New York"
        assert response.city.country == "USA"
        assert response.is_cancelled is False

    def test_venue_capacity_defaults_to_none_when_omitted(self):
        response = ConcertNextResponse(
            id=2,
            date_time=datetime(2024, 8, 1, 19, 30, 0),
            is_cancelled=False,
            venue=NextConcertVenue(name="Red Rocks Amphitheatre"),
            city=NextConcertCity(name="Morrison", country="USA"),
        )

        assert response.venue.capacity is None
