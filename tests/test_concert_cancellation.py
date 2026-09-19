"""Tests for cancellation display (badge + reason) on the concert card and
detail templates, the include_cancelled list filter, and the hide-cancelled
checkbox wired into the dashboard shell."""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _make_tour(db_session, name="Cancellation Tour"):
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=30)).date(),
        status="active",
    )


def test_dashboard_concerts_shows_cancellation_badge_and_reason(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        is_cancelled=True, cancellation_reason="Artist illness",
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "Annulé" in response.text
    assert "Artist illness" in response.text


def test_dashboard_concerts_hides_badge_and_reason_when_not_cancelled(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Active Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "Annulé" not in response.text


def test_dashboard_concerts_escapes_cancellation_reason(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "XSS Cancellation Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        is_cancelled=True, cancellation_reason="<script>alert('xss')</script>",
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text


def test_dashboard_concerts_default_includes_cancelled(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Mixed Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        is_cancelled=True, cancellation_reason="Weather",
    )
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now(),
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert response.text.count("concert-card") >= 2
    assert "Annulé" in response.text


def test_dashboard_concerts_include_cancelled_false_hides_cancelled(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Filter Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        is_cancelled=True, cancellation_reason="Weather",
    )
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now(),
    )

    response = client.get("/api/v1/dashboard/concerts", params={"include_cancelled": "false"})

    assert response.status_code == 200
    assert "Annulé" not in response.text


def test_dashboard_concerts_include_cancelled_true_restores_cancelled(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Restore Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        is_cancelled=True, cancellation_reason="Weather",
    )

    response = client.get("/api/v1/dashboard/concerts", params={"include_cancelled": "true"})

    assert response.status_code == 200
    assert "Annulé" in response.text


def test_dashboard_shell_has_hide_cancelled_checkbox_wired_to_filter(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert 'id="hide-cancelled-checkbox"' in response.text
    assert 'name="include_cancelled"' in response.text
    assert "Masquer les dates annulées" in response.text
    assert "/api/v1/dashboard/concerts" in response.text


def test_concert_detail_shows_cancellation_badge_and_reason(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Detail Cancellation Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        is_cancelled=True, cancellation_reason="Venue flooding",
    )

    response = client.get(f"/concerts/{concert.id}")

    assert response.status_code == 200
    assert "Annulé" in response.text
    assert "Venue flooding" in response.text


def test_concert_detail_hides_badge_and_reason_when_not_cancelled(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Detail Active Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
    )

    response = client.get(f"/concerts/{concert.id}")

    assert response.status_code == 200
    assert "Annulé" not in response.text


def test_concert_detail_escapes_cancellation_reason(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Detail XSS Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        is_cancelled=True, cancellation_reason="<script>alert('xss')</script>",
    )

    response = client.get(f"/concerts/{concert.id}")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text
