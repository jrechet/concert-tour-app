"""Tests for `GET /api/v1/stats/weekdays`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

# 2024-06-17 is a Monday.
BASE_TIME = datetime(2024, 6, 17, 20, 0, 0)

WEEKDAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _seed_tour(db_session):
    return create_tour(
        db_session,
        name="Weekday Stats Tour",
        artist="Test Artist",
        start_date=BASE_TIME.date(),
        end_date=BASE_TIME.date(),
        status="active",
    )


class TestWeekdayStatsEndpoint:
    """Coverage for `GET /api/v1/stats/weekdays`."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/stats/weekdays")
        assert response.status_code == 200

    def test_response_contains_exactly_seven_ordered_weekday_keys(self, client):
        response = client.get("/api/v1/stats/weekdays")
        data = response.json()
        assert list(data.keys()) == WEEKDAY_KEYS

    def test_no_concerts_yields_all_zero_counts(self, client):
        response = client.get("/api/v1/stats/weekdays")
        data = response.json()
        assert data == {day: 0 for day in WEEKDAY_KEYS}

    def test_non_cancelled_concerts_counted_on_correct_weekday(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=2)
        # BASE_TIME + 0 days = Monday, + 2 days = Wednesday.
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="50.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=2, ticket_price="50.00", base_time=BASE_TIME)

        response = client.get("/api/v1/stats/weekdays")

        assert response.status_code == 200
        data = response.json()
        assert data["monday"] == 1
        assert data["wednesday"] == 1
        for day in ["tuesday", "thursday", "friday", "saturday", "sunday"]:
            assert data[day] == 0

    def test_cancelled_concerts_excluded_from_weekday_count(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=2)
        # BASE_TIME + 4 days = Friday.
        create_concert(
            db_session, tour, venues[0], day_offset=4, ticket_price="50.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Weather",
        )
        create_concert(db_session, tour, venues[1], day_offset=4, ticket_price="50.00", base_time=BASE_TIME)

        response = client.get("/api/v1/stats/weekdays")

        assert response.status_code == 200
        data = response.json()
        assert data["friday"] == 1

    def test_weekdays_with_no_concerts_present_with_zero_value(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=1)
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="50.00", base_time=BASE_TIME)

        response = client.get("/api/v1/stats/weekdays")

        data = response.json()
        assert "sunday" in data
        assert data["sunday"] == 0
