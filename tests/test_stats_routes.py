"""Tests for `GET /api/v1/stats/venues/busiest`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session, name="Busiest Venues Tour"):
    now = datetime.now()
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=now.date(),
        end_date=now.date(),
        status="active",
    )


class TestBusiestVenuesEndpoint:
    """Coverage for `GET /api/v1/stats/venues/busiest`."""

    def test_get_busiest_venues_returns_200_and_empty_list_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/venues/busiest")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_busiest_venues_returns_top_five_ordered_by_count_desc(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=7)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            for j in range(i + 1):
                create_concert(db_session, tour, venue, day_offset=j, ticket_price="50.00", base_time=base_time)

        response = client.get("/api/v1/stats/venues/busiest")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 5
        assert body == [
            {"name": venues[6].name, "city": venues[6].city, "concert_count": 7},
            {"name": venues[5].name, "city": venues[5].city, "concert_count": 6},
            {"name": venues[4].name, "city": venues[4].city, "concert_count": 5},
            {"name": venues[3].name, "city": venues[3].city, "concert_count": 4},
            {"name": venues[2].name, "city": venues[2].city, "concert_count": 3},
        ]
        assert set(body[0].keys()) == {"name", "city", "concert_count"}

    def test_get_busiest_venues_excludes_cancelled_concerts_from_count(self, client, db_session):
        tour = _seed_tour(db_session)
        venue = create_venues(db_session, count=1)[0]
        base_time = datetime.now()
        create_concert(db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time)
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.get("/api/v1/stats/venues/busiest")

        assert response.status_code == 200
        body = response.json()
        assert body == [{"name": venue.name, "city": venue.city, "concert_count": 1}]

    def test_get_busiest_venues_breaks_count_ties_by_name_ascending(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=2)
        base_time = datetime.now()
        for venue in venues:
            create_concert(db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time)
        sorted_names = sorted(venue.name for venue in venues)

        response = client.get("/api/v1/stats/venues/busiest")

        assert response.status_code == 200
        body = response.json()
        assert [entry["name"] for entry in body] == sorted_names

    def test_get_busiest_venues_ignores_unknown_query_param(self, client, db_session):
        tour = _seed_tour(db_session)
        venue = create_venues(db_session, count=1)[0]
        create_concert(db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=datetime.now())

        response = client.get("/api/v1/stats/venues/busiest", params={"unknown": "value"})

        assert response.status_code == 200
        assert response.json() == [{"name": venue.name, "city": venue.city, "concert_count": 1}]

    def test_busiest_venues_route_appears_in_openapi_schema(self, client):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert "/api/v1/stats/venues/busiest" in response.json()["paths"]

    def test_post_busiest_venues_returns_405(self, client):
        response = client.post("/api/v1/stats/venues/busiest")

        assert response.status_code == 405

    def test_put_busiest_venues_returns_405(self, client):
        response = client.put("/api/v1/stats/venues/busiest")

        assert response.status_code == 405

    def test_delete_busiest_venues_returns_405(self, client):
        response = client.delete("/api/v1/stats/venues/busiest")

        assert response.status_code == 405
