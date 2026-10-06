"""Unit tests for `list_artists_with_tour_counts`."""

from datetime import date

from src.services.artist_service import list_artists_with_tour_counts
from tests.fixtures.dashboard_fixtures import create_tour


class TestListArtistsWithTourCounts:
    """Coverage for `list_artists_with_tour_counts`."""

    def test_multiple_artists_each_with_different_tour_counts(self, db_session):
        create_tour(db_session, "Dawn Tour", "Aurora Belle", date(2024, 1, 1), date(2024, 1, 5), "completed")
        create_tour(db_session, "Dusk Tour", "Aurora Belle", date(2024, 2, 1), date(2024, 2, 5), "completed")
        create_tour(db_session, "Solo World Tour", "Midnight Echo", date(2024, 3, 1), date(2024, 3, 5), "completed")

        result = list_artists_with_tour_counts(db_session)

        assert result == [("Aurora Belle", 2), ("Midnight Echo", 1)]

    def test_same_artist_on_several_tours_counted_once_with_total(self, db_session):
        create_tour(db_session, "Leg One", "The Night Owls", date(2024, 1, 1), date(2024, 1, 5), "completed")
        create_tour(db_session, "Leg Two", "The Night Owls", date(2024, 2, 1), date(2024, 2, 5), "completed")
        create_tour(db_session, "Leg Three", "The Night Owls", date(2024, 3, 1), date(2024, 3, 5), "completed")

        result = list_artists_with_tour_counts(db_session)

        assert result == [("The Night Owls", 3)]

    def test_no_tours_returns_empty_list(self, db_session):
        result = list_artists_with_tour_counts(db_session)

        assert result == []

    def test_mixed_case_artist_names_sort_case_insensitively(self, db_session):
        create_tour(db_session, "Tour A", "zebra Collective", date(2024, 1, 1), date(2024, 1, 5), "completed")
        create_tour(db_session, "Tour B", "Antler Brothers", date(2024, 2, 1), date(2024, 2, 5), "completed")
        create_tour(db_session, "Tour C", "mango Sunrise", date(2024, 3, 1), date(2024, 3, 5), "completed")

        result = list_artists_with_tour_counts(db_session)

        assert [artist for artist, _ in result] == [
            "Antler Brothers",
            "mango Sunrise",
            "zebra Collective",
        ]
