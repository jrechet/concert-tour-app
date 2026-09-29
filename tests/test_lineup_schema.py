"""
Unit tests for the LineupEntryCreate/LineupEntryOut Pydantic schemas.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.schemas.lineup import LineupEntryCreate, LineupEntryOut


class TestLineupEntryCreate:
    """Test cases for the LineupEntryCreate schema."""

    def test_valid_lineup_entry_create(self):
        entry = LineupEntryCreate(artist_name="The Openers", set_order=1)
        assert entry.artist_name == "The Openers"
        assert entry.set_order == 1

    def test_artist_name_is_trimmed(self):
        entry = LineupEntryCreate(artist_name="  The Openers  ", set_order=1)
        assert entry.artist_name == "The Openers"

    def test_blank_artist_name_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupEntryCreate(artist_name="   ", set_order=1)

    def test_empty_artist_name_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupEntryCreate(artist_name="", set_order=1)

    def test_set_order_must_be_at_least_one(self):
        with pytest.raises(ValidationError):
            LineupEntryCreate(artist_name="The Openers", set_order=0)

    def test_negative_set_order_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupEntryCreate(artist_name="The Openers", set_order=-1)

    def test_set_order_must_be_an_integer(self):
        with pytest.raises(ValidationError):
            LineupEntryCreate(artist_name="The Openers", set_order="first")


class TestLineupEntryOut:
    """Test cases for the LineupEntryOut schema."""

    def test_valid_lineup_entry_out(self):
        entry = LineupEntryOut(
            id=1,
            concert_id=2,
            artist_name="The Openers",
            set_order=1,
            created_at=datetime(2026, 9, 29, 0, 0, 0),
        )
        assert entry.id == 1
        assert entry.concert_id == 2
        assert entry.artist_name == "The Openers"
        assert entry.set_order == 1
        assert entry.created_at == datetime(2026, 9, 29, 0, 0, 0)

    def test_missing_required_field_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupEntryOut(id=1, concert_id=2, artist_name="The Openers", set_order=1)

    def test_reads_from_model_attributes(self):
        """Mirrors how FastAPI serializes a `response_model` from an ORM
        object: attribute access rather than dict keys."""
        class FakeOrmObject:
            id = 1
            concert_id = 2
            artist_name = "The Openers"
            set_order = 1
            created_at = datetime(2026, 9, 29, 0, 0, 0)

        entry = LineupEntryOut.model_validate(FakeOrmObject(), from_attributes=True)
        assert entry.artist_name == "The Openers"
