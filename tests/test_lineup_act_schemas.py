"""
Unit tests for the LineupActCreate/LineupActRead Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.schemas.lineup_act import ARTIST_NAME_MAX_LENGTH, LineupActCreate, LineupActRead


class TestLineupActCreate:
    """Test cases for the LineupActCreate schema."""

    def test_valid_lineup_act_create(self):
        act = LineupActCreate(artist_name="Support Band", set_order=2)
        assert act.artist_name == "Support Band"
        assert act.set_order == 2

    def test_artist_name_is_trimmed(self):
        act = LineupActCreate(artist_name="  Support Band  ", set_order=2)
        assert act.artist_name == "Support Band"

    def test_missing_artist_name_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(set_order=2)

    def test_empty_artist_name_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(artist_name="", set_order=2)

    def test_whitespace_only_artist_name_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(artist_name="   ", set_order=2)

    def test_over_max_length_artist_name_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(artist_name="a" * (ARTIST_NAME_MAX_LENGTH + 1), set_order=2)

    def test_missing_set_order_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(artist_name="Support Band")

    def test_set_order_zero_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(artist_name="Support Band", set_order=0)

    def test_negative_set_order_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(artist_name="Support Band", set_order=-1)

    def test_non_integer_set_order_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupActCreate(artist_name="Support Band", set_order="second")


class TestLineupActRead:
    """Test cases for the LineupActRead schema."""

    def test_reads_from_orm_attributes(self):
        class FakeLineupAct:
            id = 1
            concert_id = 2
            artist_name = "Support Band"
            set_order = 2

        act = LineupActRead.model_validate(FakeLineupAct())
        assert act.model_dump() == {
            "id": 1,
            "concert_id": 2,
            "artist_name": "Support Band",
            "set_order": 2,
        }
