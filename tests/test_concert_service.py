"""Tests for `list_concerts`' optional city filter."""

from datetime import datetime

import pytest

from src.services.concerts_service import MAX_CITY_QUERY_LENGTH, list_concerts
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _seed(db_session):
    """Two concerts in distinct cities (New York, London), linked via real FKs."""
    venues = create_venues(db_session, count=2)
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    new_york_concert = create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="50.00", base_time=BASE_TIME)
    london_concert = create_concert(db_session, tour, venues[1], day_offset=0, ticket_price="60.00", base_time=BASE_TIME)
    return new_york_concert, london_concert, venues


def test_list_concerts_with_no_filter_returns_all_in_date_order(db_session):
    new_york_concert, london_concert, _ = _seed(db_session)

    result = list_concerts(db_session)

    assert [c.id for c in result] == [london_concert.id, new_york_concert.id]


def test_list_concerts_city_none_returns_all_in_date_order(db_session):
    new_york_concert, london_concert, _ = _seed(db_session)

    result = list_concerts(db_session, city=None)

    assert [c.id for c in result] == [london_concert.id, new_york_concert.id]


def test_list_concerts_filters_by_exact_case_city(db_session):
    new_york_concert, _london_concert, venues = _seed(db_session)

    result = list_concerts(db_session, city=venues[0].city)

    assert [c.id for c in result] == [new_york_concert.id]


def test_list_concerts_filters_case_insensitively(db_session):
    new_york_concert, _london_concert, venues = _seed(db_session)

    result = list_concerts(db_session, city=venues[0].city.upper())

    assert [c.id for c in result] == [new_york_concert.id]


def test_list_concerts_matches_partial_city_substring(db_session):
    new_york_concert, _london_concert, venues = _seed(db_session)
    partial = venues[0].city[:3]

    result = list_concerts(db_session, city=partial)

    assert [c.id for c in result] == [new_york_concert.id]


def test_list_concerts_no_match_returns_empty_list(db_session):
    _seed(db_session)

    result = list_concerts(db_session, city="Nowhereville")

    assert result == []


def test_list_concerts_strips_surrounding_whitespace(db_session):
    new_york_concert, _london_concert, venues = _seed(db_session)

    result = list_concerts(db_session, city=f"  {venues[0].city}  ")

    assert [c.id for c in result] == [new_york_concert.id]


def test_list_concerts_empty_string_behaves_like_no_filter(db_session):
    new_york_concert, london_concert, _ = _seed(db_session)

    result = list_concerts(db_session, city="")

    assert [c.id for c in result] == [london_concert.id, new_york_concert.id]


def test_list_concerts_whitespace_only_behaves_like_no_filter(db_session):
    new_york_concert, london_concert, _ = _seed(db_session)

    result = list_concerts(db_session, city="   ")

    assert [c.id for c in result] == [london_concert.id, new_york_concert.id]


def test_list_concerts_over_length_city_raises_value_error(db_session):
    _seed(db_session)
    too_long = "a" * (MAX_CITY_QUERY_LENGTH + 1)

    with pytest.raises(ValueError):
        list_concerts(db_session, city=too_long)
