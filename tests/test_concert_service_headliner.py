"""Tests for `get_headliner`: the lineup's highest `set_order` act, and the
`HeadlinerResponse` schema it is meant to serialise into."""

from datetime import datetime

import pytest

from src.models import LineupEntry
from src.schemas import HeadlinerResponse
from src.services.concert_service import EmptyLineupError, get_headliner
from src.services.concerts_service import ConcertNotFoundError
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _create_concert(db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    return create_concert(db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME)


def _add_entry(db_session, concert, artist_name, set_order):
    entry = LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


class TestGetHeadliner:
    def test_returns_act_with_greatest_set_order_regardless_of_insertion_order(self, db_session):
        concert = _create_concert(db_session)
        _add_entry(db_session, concert, "Plays Third", set_order=3)
        _add_entry(db_session, concert, "Plays First", set_order=1)
        _add_entry(db_session, concert, "Plays Second", set_order=2)

        headliner = get_headliner(db_session, concert.id)

        assert headliner.artist_name == "Plays Third"
        assert headliner.set_order == 3

    def test_single_act_lineup_returns_that_act_at_set_order_one(self, db_session):
        concert = _create_concert(db_session)
        _add_entry(db_session, concert, "Solo Act", set_order=1)

        headliner = get_headliner(db_session, concert.id)

        assert headliner.artist_name == "Solo Act"
        assert headliner.set_order == 1

    def test_unknown_concert_raises_concert_not_found_error(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            get_headliner(db_session, 999)

    def test_existing_concert_with_empty_lineup_raises_empty_lineup_error(self, db_session):
        concert = _create_concert(db_session)

        with pytest.raises(EmptyLineupError):
            get_headliner(db_session, concert.id)

    def test_another_concerts_lineup_does_not_leak_into_the_result(self, db_session):
        concert_a = _create_concert(db_session)
        concert_b = _create_concert(db_session)
        _add_entry(db_session, concert_a, "Act A", set_order=1)
        _add_entry(db_session, concert_b, "Act B", set_order=5)

        headliner = get_headliner(db_session, concert_a.id)

        assert headliner.artist_name == "Act A"
        assert headliner.set_order == 1


class TestHeadlinerResponse:
    def test_serialises_name_and_set_position_from_the_act(self, db_session):
        concert = _create_concert(db_session)
        entry = _add_entry(db_session, concert, "The Main Act", set_order=3)

        response = HeadlinerResponse.model_validate(entry)

        assert response.model_dump() == {"name": "The Main Act", "set_position": 3}
