"""Unit tests for `list_venues` and `get_venue_with_upcoming_concerts`."""

from datetime import datetime, timedelta

import pytest

from src.crud.venue import get_venue_with_upcoming_concerts
from src.models import Venue
from src.services.venue_service import list_venues
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2026, 6, 1, 12, 0, 0)


def _create_venue(db_session, name, city, country, capacity):
    """Persist and return a `Venue` row."""
    venue = Venue(name=name, city=city, country=country, capacity=capacity)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return venue


class TestListVenues:
    """Coverage for `list_venues`."""

    def test_empty_table_returns_empty_list(self, db_session):
        assert list_venues(db_session) == []

    def test_returns_venues_sorted_by_name_regardless_of_insertion_order(self, db_session):
        _create_venue(db_session, "Tokyo Dome", "Tokyo", "Japan", 42000)
        _create_venue(db_session, "Accor Arena", "Paris", "France", 15000)
        _create_venue(db_session, "Massey Hall", "Toronto", "Canada", 2765)

        result = list_venues(db_session)

        assert [venue.name for venue in result] == [
            "Accor Arena", "Massey Hall", "Tokyo Dome",
        ]

    def test_min_capacity_excludes_smaller_venues_and_keeps_sort_order(self, db_session):
        _create_venue(db_session, "Ryman Auditorium", "Nashville", "USA", 2362)
        _create_venue(db_session, "United Center", "Chicago", "USA", 23500)
        _create_venue(db_session, "Sydney Opera House", "Sydney", "Australia", 2679)

        result = list_venues(db_session, min_capacity=2500)

        assert [venue.name for venue in result] == [
            "Sydney Opera House", "United Center",
        ]

    def test_min_capacity_zero_returns_everything(self, db_session):
        _create_venue(db_session, "Ryman Auditorium", "Nashville", "USA", 2362)
        _create_venue(db_session, "United Center", "Chicago", "USA", 23500)

        result = list_venues(db_session, min_capacity=0)

        assert [venue.name for venue in result] == [
            "Ryman Auditorium", "United Center",
        ]

    def test_negative_min_capacity_raises_value_error(self, db_session):
        with pytest.raises(ValueError):
            list_venues(db_session, min_capacity=-1)


def _make_tour(db_session):
    """Persist and return a `Tour` row spanning `REFERENCE_TIME`."""
    return create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (REFERENCE_TIME - timedelta(days=60)).date(),
        (REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )


class TestGetVenueWithUpcomingConcerts:
    """Coverage for `get_venue_with_upcoming_concerts`."""

    def test_returns_venue_fields(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = get_venue_with_upcoming_concerts(db_session, venue.id, reference_time=REFERENCE_TIME)

        assert result is not None
        assert result.id == venue.id
        assert result.name == venue.name
        assert result.city == venue.city
        assert result.country == venue.country
        assert result.capacity == venue.capacity

    def test_upcoming_concerts_sorted_soonest_first(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        later_concert = create_concert(
            db_session, tour, venue, day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME,
        )
        soonest_concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME,
        )
        middle_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = get_venue_with_upcoming_concerts(db_session, venue.id, reference_time=REFERENCE_TIME)

        assert [concert.id for concert in result.concerts] == [
            soonest_concert.id, middle_concert.id, later_concert.id,
        ]

    def test_excludes_cancelled_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        cancelled_concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )
        active_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = get_venue_with_upcoming_concerts(db_session, venue.id, reference_time=REFERENCE_TIME)

        returned_ids = [concert.id for concert in result.concerts]
        assert returned_ids == [active_concert.id]
        assert cancelled_concert.id not in returned_ids

    def test_excludes_past_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        past_concert = create_concert(
            db_session, tour, venue, day_offset=-10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )
        future_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = get_venue_with_upcoming_concerts(db_session, venue.id, reference_time=REFERENCE_TIME)

        returned_ids = [concert.id for concert in result.concerts]
        assert returned_ids == [future_concert.id]
        assert past_concert.id not in returned_ids

    def test_excludes_concerts_of_other_venues(self, db_session):
        venue, other_venue = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        own_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )
        other_venue_concert = create_concert(
            db_session, tour, other_venue, day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = get_venue_with_upcoming_concerts(db_session, venue.id, reference_time=REFERENCE_TIME)

        returned_ids = [concert.id for concert in result.concerts]
        assert returned_ids == [own_concert.id]
        assert other_venue_concert.id not in returned_ids

    def test_returns_empty_list_when_no_upcoming_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        create_concert(
            db_session, tour, venue, day_offset=-5, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = get_venue_with_upcoming_concerts(db_session, venue.id, reference_time=REFERENCE_TIME)

        assert result is not None
        assert result.concerts == []

    def test_returns_none_for_unknown_venue_id(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        unknown_venue_id = venue.id + 1

        while db_session.query(Venue).filter(Venue.id == unknown_venue_id).first() is not None:
            unknown_venue_id += 1

        result = get_venue_with_upcoming_concerts(db_session, unknown_venue_id, reference_time=REFERENCE_TIME)

        assert result is None
