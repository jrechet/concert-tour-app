"""Tests for `GET /api/v1/tours/search`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_tour_with_concert(db_session, name, artist, status="active"):
    venues = create_venues(db_session, count=1)
    tour = create_tour(
        db_session, name, artist, BASE_TIME.date(), BASE_TIME.date(), status,
    )
    create_concert(
        db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME,
    )
    return tour


class TestSearchToursEndpoint:
    """Coverage for `GET /api/v1/tours/search`."""

    def test_search_returns_200_with_matching_tours(self, client, db_session):
        tour = _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get("/api/v1/tours/search", params={"artist": "queen"})

        assert response.status_code == 200
        data = response.json()
        assert [t["id"] for t in data] == [tour.id]
        assert data[0]["artist"] == "Queen"

    def test_search_is_case_insensitive(self, client, db_session):
        tour = _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get("/api/v1/tours/search", params={"artist": "QUEEN"})

        assert response.status_code == 200
        assert [t["id"] for t in response.json()] == [tour.id]

    def test_search_matches_substring(self, client, db_session):
        tour = _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get("/api/v1/tours/search", params={"artist": "uee"})

        assert response.status_code == 200
        assert [t["id"] for t in response.json()] == [tour.id]

    def test_search_missing_artist_param_returns_422(self, client, db_session):
        _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get("/api/v1/tours/search")

        assert response.status_code == 422

    def test_search_empty_artist_param_returns_422(self, client, db_session):
        _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get("/api/v1/tours/search", params={"artist": ""})

        assert response.status_code == 422

    def test_search_no_match_returns_200_empty_list(self, client, db_session):
        _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get("/api/v1/tours/search", params={"artist": "nosuchband"})

        assert response.status_code == 200
        assert response.json() == []

    def test_search_route_not_shadowed_by_id_route(self, client, db_session):
        _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get("/api/v1/tours/search", params={"artist": "queen"})

        assert response.status_code != 404

    def test_get_tour_by_id_still_works_for_existing_tour(self, client, db_session):
        tour = _make_tour_with_concert(db_session, "Royal Tour", "Queen")

        response = client.get(f"/api/v1/tours/{tour.id}")

        assert response.status_code == 200
        assert response.json()["id"] == tour.id

    def test_get_tour_by_id_returns_404_for_unknown_id(self, client):
        response = client.get("/api/v1/tours/999999")

        assert response.status_code == 404
