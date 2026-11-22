"""Unit tests for `search_venues`, independent of the HTTP layer."""

import pytest

from src.models import Venue
from src.services.venue_service import search_venues


def _create_venue(db_session, name, city, country="USA", capacity=10000):
    """Persist and return a `Venue` row."""
    venue = Venue(name=name, city=city, country=country, capacity=capacity)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return venue


class TestSearchVenues:
    """Coverage for `search_venues`."""

    def test_name_substring_match(self, db_session):
        matching = _create_venue(db_session, "Accor Arena", "Paris")
        _create_venue(db_session, "Massey Hall", "Toronto")

        result = search_venues(db_session, "Arena")

        assert [v.id for v in result] == [matching.id]

    def test_city_substring_match(self, db_session):
        matching = _create_venue(db_session, "Madison Square Garden", "New York")
        _create_venue(db_session, "Massey Hall", "Toronto")

        result = search_venues(db_session, "York")

        assert [v.id for v in result] == [matching.id]

    @pytest.mark.parametrize("query", ["ARENA", "arena", "ArEnA"])
    def test_case_insensitive_match(self, db_session, query):
        matching = _create_venue(db_session, "Accor Arena", "Paris")

        result = search_venues(db_session, query)

        assert [v.id for v in result] == [matching.id]

    def test_results_ordered_by_name_ascending(self, db_session):
        charlie = _create_venue(db_session, "Charlie Arena", "Chicago")
        alice = _create_venue(db_session, "Alice Arena", "Austin")
        bob = _create_venue(db_session, "Bob Arena", "Boston")

        result = search_venues(db_session, "Arena")

        assert [v.id for v in result] == [alice.id, bob.id, charlie.id]

    def test_venue_matching_both_fields_returned_once(self, db_session):
        matching = _create_venue(db_session, "Arena City Hall", "Arena City")

        result = search_venues(db_session, "Arena")

        assert [v.id for v in result] == [matching.id]

    def test_no_match_returns_empty_list(self, db_session):
        _create_venue(db_session, "Accor Arena", "Paris")

        assert search_venues(db_session, "Nonexistent Venue") == []

    def test_percent_wildcard_is_matched_literally(self, db_session):
        matching = _create_venue(db_session, "100% Arena", "Paris")
        _create_venue(db_session, "Accor Arena", "Paris")

        result = search_venues(db_session, "0% A")

        assert [v.id for v in result] == [matching.id]
