"""Tests for `GET /api/v1/artists`."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from src.schemas.artist import ArtistSummary
from tests.fixtures.dashboard_fixtures import create_tour


class TestGetArtistsEndpoint:
    """Coverage for `GET /api/v1/artists`."""

    def test_returns_artists_with_tour_counts_alphabetically(self, client, db_session):
        base_time = datetime.now()
        create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            base_time.date(), base_time.date(), "active",
        )
        create_tour(
            db_session, "Encore Tour", "Aurora Belle",
            base_time.date(), base_time.date(), "planned",
        )
        create_tour(
            db_session, "Echoes Tour", "Zenith",
            base_time.date(), base_time.date(), "active",
        )

        response = client.get("/api/v1/artists")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert [artist["name"] for artist in data] == ["Aurora Belle", "Zenith"]
        assert data == [
            {"name": "Aurora Belle", "tour_count": 2},
            {"name": "Zenith", "tour_count": 1},
        ]
        for artist in data:
            ArtistSummary.model_validate(artist)

    def test_no_tours_returns_empty_list(self, client):
        response = client.get("/api/v1/artists")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.json() == []

    def test_maps_service_result_using_mocked_service(self, client):
        mock_service = MagicMock()
        mock_service.return_value = [("Aurora Belle", 2), ("Zenith", 1)]

        with patch("src.routers.artists.list_artists_with_tour_counts", mock_service):
            response = client.get("/api/v1/artists")

        assert response.status_code == 200
        assert response.json() == [
            {"name": "Aurora Belle", "tour_count": 2},
            {"name": "Zenith", "tour_count": 1},
        ]
        mock_service.assert_called_once()
