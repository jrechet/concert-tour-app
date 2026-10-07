"""Tests for `POST /api/v1/venues`."""

from tests.fixtures.dashboard_fixtures import create_venues


def _payload(**overrides):
    payload = {
        "name": "Madison Square Garden",
        "city": "New York",
        "country": "USA",
        "capacity": 20000,
    }
    payload.update(overrides)
    return payload


class TestPostVenuesEndpoint:
    """Coverage for `POST /api/v1/venues`."""

    def test_valid_payload_returns_201_and_created_venue(self, client):
        response = client.post("/api/v1/venues", json=_payload())

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Madison Square Garden"
        assert data["city"] == "New York"
        assert data["country"] == "USA"
        assert data["capacity"] == 20000
        assert isinstance(data["id"], int)

    def test_capacity_zero_returns_422(self, client):
        response = client.post("/api/v1/venues", json=_payload(capacity=0))

        assert response.status_code == 422

    def test_capacity_negative_returns_422(self, client):
        response = client.post("/api/v1/venues", json=_payload(capacity=-1))

        assert response.status_code == 422

    def test_missing_name_returns_422(self, client):
        payload = _payload()
        del payload["name"]

        response = client.post("/api/v1/venues", json=payload)

        assert response.status_code == 422

    def test_empty_name_returns_422(self, client):
        response = client.post("/api/v1/venues", json=_payload(name=""))

        assert response.status_code == 422

    def test_duplicate_name_and_city_returns_409(self, client, db_session):
        existing = create_venues(db_session, count=1)[0]

        response = client.post(
            "/api/v1/venues",
            json=_payload(name=existing.name, city=existing.city, country="Canada", capacity=5000),
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_same_name_different_city_returns_201(self, client, db_session):
        existing = create_venues(db_session, count=1)[0]

        response = client.post(
            "/api/v1/venues",
            json=_payload(name=existing.name, city="A Different City"),
        )

        assert response.status_code == 201
        assert response.json()["city"] == "A Different City"
