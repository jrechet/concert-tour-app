"""Integration tests for `GET /api/v1/concerts/export.csv`."""

import csv
import io
from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestConcertsExportCsv:
    """Coverage for `GET /api/v1/concerts/export.csv`."""

    def test_no_concerts_returns_header_only(self, client):
        response = client.get("/api/v1/concerts/export.csv")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert response.headers["content-disposition"] == "attachment; filename=concerts.csv"
        assert response.text == "date,city,venue,tour\r\n"

    def test_rows_match_seeded_concerts(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        first = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        second = create_concert(db_session, tour, venues[1], day_offset=5, ticket_price="90.00", base_time=BASE_TIME)

        response = client.get("/api/v1/concerts/export.csv")

        assert response.status_code == 200
        rows = list(csv.reader(io.StringIO(response.text)))

        assert rows[0] == ["date", "city", "venue", "tour"]
        assert rows[1] == [first.date_time.date().isoformat(), venues[0].city, venues[0].name, tour.name]
        assert rows[2] == [second.date_time.date().isoformat(), venues[1].city, venues[1].name, tour.name]
        assert len(rows) == 3

    def test_values_with_commas_and_quotes_are_escaped(self, client, db_session):
        venues = create_venues(db_session, count=1)
        venues[0].name = 'The "Garden", Arena'
        venues[0].city = "Washington, D.C."
        db_session.commit()
        tour = create_tour(
            db_session, "Tour, With Commas", "Test Artist",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        response = client.get("/api/v1/concerts/export.csv")

        assert response.status_code == 200
        rows = list(csv.reader(io.StringIO(response.text)))

        assert rows[1] == [concert.date_time.date().isoformat(), venues[0].city, venues[0].name, tour.name]
        assert '"Washington, D.C."' in response.text
        assert '"The ""Garden"", Arena"' in response.text
        assert '"Tour, With Commas"' in response.text

    def test_export_route_does_not_conflict_with_concert_id_route(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Solo Tour", "Test Artist",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        export_response = client.get("/api/v1/concerts/export.csv")
        detail_response = client.get(f"/api/v1/concerts/{concert.id}")

        assert export_response.status_code == 200
        assert export_response.headers["content-type"].startswith("text/csv")
        assert detail_response.status_code == 200
        assert detail_response.json()["id"] == concert.id
