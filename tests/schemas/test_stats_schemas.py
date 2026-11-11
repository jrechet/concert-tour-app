"""
Unit tests for the `CityRevenue` Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import ArtistConcertCount, CityRevenue


class TestCityRevenue:
    """Test cases for the `CityRevenue` schema."""

    def test_valid_payload_round_trips_through_model_dump(self):
        item = CityRevenue(city="Paris", revenue=1500)
        assert item.model_dump() == {"city": "Paris", "revenue": 1500}

    def test_zero_revenue_is_accepted(self):
        item = CityRevenue(city="Paris", revenue=0)
        assert item.revenue == 0

    def test_none_revenue_raises(self):
        with pytest.raises(ValidationError):
            CityRevenue(city="Paris", revenue=None)

    def test_missing_city_raises(self):
        with pytest.raises(ValidationError):
            CityRevenue(revenue=1500)


class ArtistRow:
    """Simple attribute-carrying object mimicking an ORM aggregate row."""

    def __init__(self, artist_id, name, concert_count):
        self.artist_id = artist_id
        self.name = name
        self.concert_count = concert_count


class TestArtistConcertCount:
    """Test cases for the `ArtistConcertCount` schema."""

    def test_valid_payload_round_trips_through_model_dump(self):
        item = ArtistConcertCount(artist_id=1, name="The Rolling Stones", concert_count=12)
        assert item.model_dump() == {
            "artist_id": 1,
            "name": "The Rolling Stones",
            "concert_count": 12,
        }

    def test_negative_concert_count_raises(self):
        with pytest.raises(ValidationError):
            ArtistConcertCount(artist_id=1, name="The Rolling Stones", concert_count=-1)

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ArtistConcertCount(artist_id=1, concert_count=12)

    def test_builds_from_attribute_carrying_object(self):
        row = ArtistRow(artist_id=2, name="Daft Punk", concert_count=7)
        item = ArtistConcertCount.model_validate(row)
        assert item.model_dump() == {
            "artist_id": 2,
            "name": "Daft Punk",
            "concert_count": 7,
        }
