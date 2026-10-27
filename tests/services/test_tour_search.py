"""Unit tests for `search_tours_by_artist`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.services.tour_service import search_tours_by_artist
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestSearchToursByArtist:
    """Coverage for `search_tours_by_artist`."""

    def _make_tour_with_concert(self, db_session, name, artist, status="active"):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, name, artist, BASE_TIME.date(), BASE_TIME.date(), status,
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME,
        )
        return tour

    @pytest.mark.parametrize("query", ["queen", "QUEEN", "QuEeN"])
    def test_case_insensitive_match(self, db_session, query):
        tour = self._make_tour_with_concert(db_session, "Royal Tour", "Queen")

        result = search_tours_by_artist(db_session, query)

        assert [t.id for t in result] == [tour.id]

    def test_substring_match_mid_word(self, db_session):
        tour = self._make_tour_with_concert(db_session, "Royal Tour", "Queen")

        result = search_tours_by_artist(db_session, "uee")

        assert [t.id for t in result] == [tour.id]

    def test_no_match_returns_empty_list(self, db_session):
        self._make_tour_with_concert(db_session, "Royal Tour", "Queen")

        assert search_tours_by_artist(db_session, "Nonexistent Artist") == []

    def test_empty_input_returns_empty_list(self, db_session):
        self._make_tour_with_concert(db_session, "Royal Tour", "Queen")

        assert search_tours_by_artist(db_session, "") == []

    def test_percent_wildcard_is_matched_literally(self, db_session):
        matching = self._make_tour_with_concert(db_session, "Discount Tour", "100% Queen")
        self._make_tour_with_concert(db_session, "Royal Tour", "Queen")

        result = search_tours_by_artist(db_session, "0% Q")

        assert [t.id for t in result] == [matching.id]

    def test_underscore_wildcard_is_matched_literally(self, db_session):
        matching = self._make_tour_with_concert(db_session, "Fan Tour", "Queen_Fans")
        self._make_tour_with_concert(db_session, "Royal Tour", "Queen Fans")

        result = search_tours_by_artist(db_session, "n_F")

        assert [t.id for t in result] == [matching.id]

    def test_results_are_ordered_by_artist_then_id(self, db_session):
        charlie = self._make_tour_with_concert(db_session, "Tour C", "Charlie Queenson")
        alice = self._make_tour_with_concert(db_session, "Tour A", "Alice Queenston")
        bob = self._make_tour_with_concert(db_session, "Tour B", "Bob Queentin")

        result = search_tours_by_artist(db_session, "queen")

        assert [t.id for t in result] == [alice.id, bob.id, charlie.id]

    def test_results_capped_by_limit(self, db_session):
        tours = [
            self._make_tour_with_concert(db_session, f"Tour {i}", f"Queen Tribute {i}")
            for i in range(5)
        ]

        result = search_tours_by_artist(db_session, "queen", limit=2)

        assert [t.id for t in result] == [tours[0].id, tours[1].id]
