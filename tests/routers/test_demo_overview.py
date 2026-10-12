"""Tests for `GET /api/v1/demo/tour-overview`, exercised through the HTTP
client (the public interface) rather than calling `src.routers.demo`'s
helper logic directly."""

from datetime import date

import pytest

from src import config
from src.demo import config as demo_config
from src.demo.dataset import build_demo_dataset
from src.demo.seeder import seed_demo

ENDPOINT = "/api/v1/demo/tour-overview"


@pytest.fixture(autouse=True)
def demo_enabled(monkeypatch):
    """Enable the demo feature flag for every test in this module, except
    the one that explicitly disables it."""
    monkeypatch.setattr(config, "DEMO_ENABLED", True)


def _seed(db_session):
    seed_demo(db_session)
    db_session.commit()


class TestDemoTourOverviewEndpoint:
    def test_overview_returns_200_with_full_tour(self, client, db_session):
        _seed(db_session)

        response = client.get(ENDPOINT)

        assert response.status_code == 200
        data = response.json()
        assert data["tour_name"] == demo_config.DEMO_TOUR_NAME
        assert data["concert_count"] == demo_config.DEMO_VENUE_COUNT
        assert len(data["concerts"]) == demo_config.DEMO_VENUE_COUNT
        for concert in data["concerts"]:
            assert concert["venue_name"]
            assert concert["city"]
            assert len(concert["ticket_tiers"]) == len(demo_config.DEMO_TICKET_TIER_NAMES)

    def test_overview_returns_404_when_not_seeded(self, client):
        response = client.get(ENDPOINT)

        assert response.status_code == 404
        assert response.json()["detail"]

    def test_overview_returns_403_when_demo_disabled(self, client, db_session, monkeypatch):
        _seed(db_session)
        monkeypatch.setattr(config, "DEMO_ENABLED", False)

        response = client.get(ENDPOINT)

        assert response.status_code == 403

    def test_city_filter_returns_only_matching_concerts(self, client, db_session):
        _seed(db_session)
        dataset = build_demo_dataset()
        target_city = dataset.venues[0].city

        response = client.get(ENDPOINT, params={"city": target_city.upper()})

        assert response.status_code == 200
        data = response.json()
        assert len(data["concerts"]) == 1
        assert data["concerts"][0]["city"] == target_city

    def test_unknown_city_returns_200_empty_list(self, client, db_session):
        _seed(db_session)

        response = client.get(ENDPOINT, params={"city": "Nowhereville"})

        assert response.status_code == 200
        assert response.json()["concerts"] == []

    def test_blank_city_returns_422(self, client, db_session):
        _seed(db_session)

        response = client.get(ENDPOINT, params={"city": "   "})

        assert response.status_code == 422

    def test_past_and_upcoming_counts(self, client, db_session):
        _seed(db_session)
        dataset = build_demo_dataset()
        today = date.today()
        expected_past = sum(1 for concert in dataset.concerts if concert.date_time.date() < today)
        expected_upcoming = sum(1 for concert in dataset.concerts if concert.date_time.date() >= today)

        response = client.get(ENDPOINT)

        assert response.status_code == 200
        data = response.json()
        assert data["past_concert_count"] == expected_past
        assert data["upcoming_concert_count"] == expected_upcoming
        assert data["past_concert_count"] + data["upcoming_concert_count"] == data["concert_count"]
