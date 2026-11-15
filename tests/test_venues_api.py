"""Tests for `PATCH /api/v1/venues/{venue_id}`."""

from src.main import app
from tests.fixtures.dashboard_fixtures import create_venues


def test_route_is_registered_on_the_app():
    schema = app.openapi()
    assert "patch" in schema["paths"]["/api/v1/venues/{venue_id}"]


def test_updates_name_only_returns_200_with_other_fields_unchanged(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"name": "New Name"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == venue.id
    assert body["name"] == "New Name"
    assert body["city"] == venue.city
    assert body["country"] == venue.country
    assert body["capacity"] == venue.capacity


def test_updates_city_only_returns_200_with_other_fields_unchanged(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"city": "New City"})

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "New City"
    assert body["name"] == venue.name
    assert body["country"] == venue.country
    assert body["capacity"] == venue.capacity


def test_updates_country_only_returns_200_with_other_fields_unchanged(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"country": "New Country"})

    assert response.status_code == 200
    body = response.json()
    assert body["country"] == "New Country"
    assert body["name"] == venue.name
    assert body["city"] == venue.city
    assert body["capacity"] == venue.capacity


def test_updates_capacity_only_returns_200_with_other_fields_unchanged(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"capacity": 99999})

    assert response.status_code == 200
    body = response.json()
    assert body["capacity"] == 99999
    assert body["name"] == venue.name
    assert body["city"] == venue.city
    assert body["country"] == venue.country


def test_updates_multiple_fields_at_once_returns_200(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(
        f"/api/v1/venues/{venue.id}",
        json={"name": "New Name", "city": "New City", "country": "New Country", "capacity": 12345},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["city"] == "New City"
    assert body["country"] == "New Country"
    assert body["capacity"] == 12345


def test_zero_capacity_returns_422(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"capacity": 0})

    assert response.status_code == 422


def test_negative_capacity_returns_422(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"capacity": -1})

    assert response.status_code == 422


def test_empty_name_returns_422(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"name": ""})

    assert response.status_code == 422


def test_whitespace_only_name_returns_422(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.patch(f"/api/v1/venues/{venue.id}", json={"name": "   "})

    assert response.status_code == 422


def test_duplicate_name_and_city_returns_409(client, db_session):
    venue, other_venue = create_venues(db_session, count=2)

    response = client.patch(
        f"/api/v1/venues/{venue.id}",
        json={"name": other_venue.name, "city": other_venue.city},
    )

    assert response.status_code == 409


def test_unknown_venue_id_returns_404(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    unknown_venue_id = venue.id + 1

    response = client.patch(f"/api/v1/venues/{unknown_venue_id}", json={"name": "Doesn't Matter"})

    assert response.status_code == 404
