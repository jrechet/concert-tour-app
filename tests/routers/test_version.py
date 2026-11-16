"""Tests for `GET /api/v1/version`."""

from src.core.version import get_app_version


def test_version_endpoint_returns_200_and_version(client):
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json()["version"] == get_app_version()


def test_version_endpoint_requires_no_auth(client):
    response = client.get("/api/v1/version", headers={})

    assert response.status_code == 200


def test_api_root_returns_api_version(client):
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["version"] == "1"
