"""Tests for the `min_price`/`max_price` query params on GET
/api/v1/concerts: validation (422 on an invalid range or a negative value)
and pass-through acceptance (no filtering applied yet, existing behavior
unaffected).
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour_and_venue(db_session):
    tour = create_tour(
        db_session,
        name="Price Filter Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return tour, venue


def test_min_price_above_max_price_returns_422(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/concerts/", params={"min_price": 100, "max_price": 50})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("min_price" in error["msg"] and "max_price" in error["msg"] for error in detail)


def test_min_price_equal_to_max_price_is_accepted(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/concerts/", params={"min_price": 50, "max_price": 50})

    assert response.status_code == 200


def test_negative_min_price_returns_422(client, db_session):
    response = client.get("/api/v1/concerts/", params={"min_price": -1})

    assert response.status_code == 422


def test_negative_max_price_returns_422(client, db_session):
    response = client.get("/api/v1/concerts/", params={"max_price": -1})

    assert response.status_code == 422


def test_only_min_price_is_accepted(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/concerts/", params={"min_price": 10})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_only_max_price_is_accepted(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/concerts/", params={"max_price": 100})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_no_price_params_is_accepted_and_unaffected(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/concerts/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_price_params_are_documented_in_openapi_schema(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    params = response.json()["paths"]["/api/v1/concerts/"]["get"]["parameters"]
    param_names = {param["name"] for param in params}
    assert "min_price" in param_names
    assert "max_price" in param_names


def test_price_filter_does_not_actually_filter_results_yet(client, db_session):
    """Price filtering is a stub for now: providing a price range that
    would exclude every concert still returns all of them."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/concerts/", params={"min_price": 1000, "max_price": 2000})

    assert response.status_code == 200
    assert len(response.json()) == 1
