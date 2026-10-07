"""Unit tests for `list_venues`."""

import pytest

from src.models import Venue
from src.services.venue_service import list_venues


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
