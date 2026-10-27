"""
Unit tests for the tour search query and response schemas.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.schemas.tour import TourRead, TourSearchQuery


class TestTourSearchQuery:
    """Test cases for TourSearchQuery schema."""

    def test_valid_artist_is_accepted_and_stripped(self):
        query = TourSearchQuery(artist="  queen  ")
        assert query.artist == "queen"

    def test_missing_artist_raises(self):
        with pytest.raises(ValidationError):
            TourSearchQuery()

    def test_empty_artist_raises(self):
        with pytest.raises(ValidationError):
            TourSearchQuery(artist="")

    def test_whitespace_only_artist_raises(self):
        with pytest.raises(ValidationError):
            TourSearchQuery(artist="   ")


class TestTourRead:
    """Test cases for the TourRead schema reused as the search result item type."""

    def test_round_trip_from_orm_object(self):
        class TourRow:
            id = 1
            name = "World Tour 2024"
            artist = "Queen"
            start_date = date(2024, 6, 1)
            end_date = date(2024, 12, 31)
            description = "An amazing world tour"
            status = "planned"

        read = TourRead.model_validate(TourRow(), from_attributes=True)
        assert read.id == 1
        assert read.artist == "Queen"
        assert read.start_date == date(2024, 6, 1)
