"""Tests for `GET /api/v1/concerts/between`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via the
`tests/fixtures/dashboard_fixtures.py` helpers) rather than hardcoded ids.
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 18, 0, 0)


class TestGetConcertsBetween:
    """Coverage for `GET /api/v1/concerts/between`."""

    def test_valid_range_returns_concerts_soonest_first(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            (BASE_TIME - timedelta(days=10)).date(),
            (BASE_TIME + timedelta(days=10)).date(),
            "active",
        )
        before_range = create_concert(
            db_session, tour, venues[0], day_offset=-10, ticket_price="80.00", base_time=BASE_TIME
        )
        later = create_concert(
            db_session, tour, venues[1], day_offset=8, ticket_price="80.00", base_time=BASE_TIME
        )
        earliest = create_concert(
            db_session, tour, venues[2], day_offset=1, ticket_price="80.00", base_time=BASE_TIME
        )
        after_range = create_concert(
            db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=BASE_TIME
        )

        start = BASE_TIME.date()
        end = (BASE_TIME + timedelta(days=10)).date()
        response = client.get(
            "/api/v1/concerts/between", params={"start": start.isoformat(), "end": end.isoformat()}
        )

        assert response.status_code == 200
        ids = [c["id"] for c in response.json()]
        assert ids == [earliest.id, later.id]
        assert before_range.id not in ids
        assert after_range.id not in ids

    def test_concert_exactly_on_start_date_is_included(self, db_session, client):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Start Date Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        start_concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME
        )

        start = BASE_TIME.date().isoformat()
        end = (BASE_TIME + timedelta(days=5)).date().isoformat()
        response = client.get("/api/v1/concerts/between", params={"start": start, "end": end})

        assert response.status_code == 200
        assert start_concert.id in [c["id"] for c in response.json()]

    def test_concert_exactly_on_end_date_is_included(self, db_session, client):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "End Date Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        end_concert = create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=BASE_TIME
        )

        start = BASE_TIME.date().isoformat()
        end = (BASE_TIME + timedelta(days=5)).date().isoformat()
        response = client.get("/api/v1/concerts/between", params={"start": start, "end": end})

        assert response.status_code == 200
        assert end_concert.id in [c["id"] for c in response.json()]

    def test_concerts_just_outside_range_are_excluded(self, db_session, client):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Just Outside Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=-1, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=6, ticket_price="80.00", base_time=BASE_TIME)

        start = BASE_TIME.date().isoformat()
        end = (BASE_TIME + timedelta(days=5)).date().isoformat()
        response = client.get("/api/v1/concerts/between", params={"start": start, "end": end})

        assert response.status_code == 200
        assert response.json() == []

    def test_no_concerts_in_range_returns_empty_list(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Out Of Range Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=-3, ticket_price="80.00", base_time=BASE_TIME)

        start = BASE_TIME.date().isoformat()
        end = (BASE_TIME + timedelta(days=5)).date().isoformat()
        response = client.get("/api/v1/concerts/between", params={"start": start, "end": end})

        assert response.status_code == 200
        assert response.json() == []

    def test_start_equal_to_end_returns_200(self, db_session, client):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Single Day Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        on_date = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME
        )

        day = BASE_TIME.date().isoformat()
        response = client.get("/api/v1/concerts/between", params={"start": day, "end": day})

        assert response.status_code == 200
        assert [c["id"] for c in response.json()] == [on_date.id]

    def test_start_after_end_returns_422(self, client):
        start = (BASE_TIME + timedelta(days=5)).date().isoformat()
        end = BASE_TIME.date().isoformat()

        response = client.get("/api/v1/concerts/between", params={"start": start, "end": end})

        assert response.status_code == 422

    def test_missing_start_returns_422(self, client):
        end = BASE_TIME.date().isoformat()

        response = client.get("/api/v1/concerts/between", params={"end": end})

        assert response.status_code == 422

    def test_missing_end_returns_422(self, client):
        start = BASE_TIME.date().isoformat()

        response = client.get("/api/v1/concerts/between", params={"start": start})

        assert response.status_code == 422

    def test_malformed_start_date_month_out_of_range_returns_422(self, client):
        end = BASE_TIME.date().isoformat()

        response = client.get(
            "/api/v1/concerts/between", params={"start": "2026-13-01", "end": end}
        )

        assert response.status_code == 422

    def test_malformed_start_date_wrong_format_returns_422(self, client):
        end = BASE_TIME.date().isoformat()

        response = client.get(
            "/api/v1/concerts/between", params={"start": "01-02-2026", "end": end}
        )

        assert response.status_code == 422

    def test_between_does_not_resolve_to_single_concert_route(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Routing Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        start = BASE_TIME.date().isoformat()
        end = (BASE_TIME + timedelta(days=5)).date().isoformat()
        response = client.get("/api/v1/concerts/between", params={"start": start, "end": end})

        assert response.status_code == 200
        assert isinstance(response.json(), list)
