"""Unit tests for the demo dataset builder."""

from datetime import datetime, timezone
from decimal import Decimal

from src import database
from src.demo import config
from src.demo.dataset import (
    DemoBand,
    DemoTicketTier,
    DemoTour,
    build_demo_dataset,
)
from src.schemas.tour import TourStatus


def test_build_demo_dataset_returns_one_band_one_tour():
    dataset = build_demo_dataset()

    assert isinstance(dataset.band, DemoBand)
    assert isinstance(dataset.tour, DemoTour)
    assert dataset.tour.band == dataset.band


def test_concert_count_matches_configured_venue_count():
    dataset = build_demo_dataset()

    assert len(dataset.venues) == config.DEMO_VENUE_COUNT
    assert len(dataset.concerts) == config.DEMO_VENUE_COUNT

    cities = [concert.venue.city for concert in dataset.concerts]
    assert len(cities) == len(set(cities))


def test_dataset_contains_past_and_upcoming_concerts():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    dataset = build_demo_dataset(now=now)

    assert any(concert.date_time < now for concert in dataset.concerts)
    assert any(concert.date_time > now for concert in dataset.concerts)


def test_ticket_prices_come_from_config(monkeypatch):
    monkeypatch.setattr(config, "DEMO_TICKET_TIER_NAMES", ["Standard"])
    monkeypatch.setattr(config, "DEMO_TICKET_TIER_PRICES", [Decimal("42.00")])

    dataset = build_demo_dataset()

    expected = [DemoTicketTier(name="Standard", price=Decimal("42.00"))]
    for concert in dataset.concerts:
        assert concert.ticket_tiers == expected


def test_statuses_match_model_enums():
    dataset = build_demo_dataset()

    valid_statuses = {status.value for status in TourStatus}
    assert dataset.tour.status in valid_statuses


def test_build_is_pure(monkeypatch):
    calls = []
    monkeypatch.setattr(database, "SessionLocal", lambda *args, **kwargs: calls.append((args, kwargs)))
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = build_demo_dataset(now=now)
    second = build_demo_dataset(now=now)

    assert first == second
    assert calls == []
