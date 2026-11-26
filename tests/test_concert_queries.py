"""Tests for `list_concerts`' optional case-insensitive `venue` filter."""

from datetime import datetime

from src.services.concerts_service import list_concerts
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _seed(db_session):
    """Two concerts at distinct venues (Madison Square Garden, The O2 Arena),
    linked via real FKs."""
    venues = create_venues(db_session, count=2)
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    msg_concert = create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="50.00", base_time=BASE_TIME)
    o2_concert = create_concert(db_session, tour, venues[1], day_offset=0, ticket_price="60.00", base_time=BASE_TIME)
    return msg_concert, o2_concert, venues


def test_list_concerts_without_venue_returns_all(db_session):
    msg_concert, o2_concert, _ = _seed(db_session)

    result = list_concerts(db_session)

    assert [c.id for c in result] == [o2_concert.id, msg_concert.id]


def test_list_concerts_filters_by_exact_venue_name(db_session):
    msg_concert, _o2_concert, venues = _seed(db_session)

    result = list_concerts(db_session, venue=venues[0].name)

    assert [c.id for c in result] == [msg_concert.id]


def test_list_concerts_venue_match_ignores_case(db_session):
    msg_concert, _o2_concert, venues = _seed(db_session)
    assert venues[0].name == "Madison Square Garden"

    for candidate in ("madison square garden", "MADISON SQUARE GARDEN", "Madison Square Garden"):
        result = list_concerts(db_session, venue=candidate)
        assert [c.id for c in result] == [msg_concert.id]


def test_list_concerts_venue_name_is_trimmed(db_session):
    msg_concert, _o2_concert, venues = _seed(db_session)

    result = list_concerts(db_session, venue=f"  {venues[0].name}  ")

    assert [c.id for c in result] == [msg_concert.id]


def test_list_concerts_unknown_venue_returns_empty_list(db_session):
    _seed(db_session)

    result = list_concerts(db_session, venue="Nonexistent Arena")

    assert result == []


def test_list_concerts_venue_wildcard_chars_are_literal(db_session):
    _seed(db_session)

    result = list_concerts(db_session, venue="%")

    assert result == []
