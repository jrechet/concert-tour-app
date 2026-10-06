"""
Unit tests for ConcertSummary and VenueDetailResponse Pydantic schemas.
"""

from datetime import datetime
from types import SimpleNamespace

from src.schemas.venue import ConcertSummary, VenueDetailResponse


def make_concert(id=1, date_time=None, status="confirmed", artist="The Headliners"):
    """Build a Concert-ORM-like object with a nested `tour` relationship."""
    tour = SimpleNamespace(status=status, artist=artist)
    return SimpleNamespace(
        id=id,
        date_time=date_time or datetime(2024, 7, 15, 20, 0, 0),
        tour=tour,
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


class TestConcertSummary:
    """Test cases for ConcertSummary schema."""

    def test_serializes_concert_orm_object(self):
        concert = make_concert(id=7, status="confirmed", artist="The Headliners")
        summary = ConcertSummary.model_validate(concert)
        assert summary.model_dump() == {
            "id": 7,
            "date": datetime(2024, 7, 15, 20, 0, 0),
            "status": "confirmed",
            "artist": "The Headliners",
        }

    def test_accepts_plain_dict(self):
        payload = {"id": 1, "date": "2024-07-15T20:00:00", "status": "confirmed", "artist": "The Headliners"}
        summary = ConcertSummary(**payload)
        assert summary.id == 1
        assert summary.status == "confirmed"

    def test_missing_tour_defaults_status_and_artist_to_none(self):
        concert = SimpleNamespace(id=1, date_time=datetime(2024, 7, 15, 20, 0, 0), tour=None)
        summary = ConcertSummary.model_validate(concert)
        assert summary.status is None
        assert summary.artist is None


class TestVenueDetailResponse:
    """Test cases for VenueDetailResponse schema."""

    def test_serializes_venue_with_nested_concerts(self):
        concerts = [
            make_concert(id=1, status="confirmed", artist="The Headliners"),
            make_concert(id=2, date_time=datetime(2024, 8, 1, 19, 30, 0), status="planned", artist="Another Act"),
        ]
        venue = make_venue(upcoming_concerts=concerts)

        response = VenueDetailResponse.model_validate(venue)
        dumped = response.model_dump()

        assert dumped == {
            "id": 1,
            "name": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "capacity": 20000,
            "upcoming_concerts": [
                {
                    "id": 1,
                    "date": datetime(2024, 7, 15, 20, 0, 0),
                    "status": "confirmed",
                    "artist": "The Headliners",
                },
                {
                    "id": 2,
                    "date": datetime(2024, 8, 1, 19, 30, 0),
                    "status": "planned",
                    "artist": "Another Act",
                },
            ],
        }

    def test_empty_upcoming_concerts_serializes_to_empty_list(self):
        venue = make_venue(upcoming_concerts=[])

        response = VenueDetailResponse.model_validate(venue)

        assert response.upcoming_concerts == []
        assert response.model_dump()["upcoming_concerts"] == []
        assert "upcoming_concerts" in response.model_dump_json()

    def test_upcoming_concerts_defaults_to_empty_list_when_omitted(self):
        response = VenueDetailResponse(id=1, name="Arena", city="Paris", country="France", capacity=None)
        assert response.upcoming_concerts == []
