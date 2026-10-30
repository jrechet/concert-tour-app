"""Unit tests for the LineupEntryMove/LineupEntryRead Pydantic schemas."""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from src.models import LineupEntry
from src.schemas.lineup import LineupEntryMove, LineupEntryRead
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session):
    base_time = datetime(2026, 11, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=base_time.date(),
        end_date=(base_time + timedelta(days=10)).date(),
        status="planned",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )


class TestLineupEntryMove:
    """Test cases for the LineupEntryMove request schema."""

    def test_accepts_a_positive_set_order(self):
        move = LineupEntryMove(set_order=1)
        assert move.set_order == 1

    def test_accepts_another_positive_set_order(self):
        move = LineupEntryMove(set_order=5)
        assert move.set_order == 5

    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            LineupEntryMove(set_order=0)

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            LineupEntryMove(set_order=-3)

    def test_missing_set_order_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupEntryMove()

    def test_non_integer_set_order_is_rejected(self):
        with pytest.raises(ValidationError):
            LineupEntryMove(set_order="first")


class TestLineupEntryRead:
    """Test cases for the LineupEntryRead response schema."""

    def test_model_validate_round_trips_a_real_orm_entry(self, db_session):
        concert = _build_concert(db_session)
        entry = LineupEntry(concert_id=concert.id, artist_name="The Openers", set_order=1)
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        read = LineupEntryRead.model_validate(entry)

        assert read.id == entry.id
        assert read.concert_id == concert.id
        assert read.artist_name == "The Openers"
        assert read.set_order == 1
        assert read.created_at == entry.created_at
