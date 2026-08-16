"""Tests for the realistic multi-concert tour test fixtures.

The dashboard feature itself isn't implemented on `main` yet, so these tests
don't hit a dashboard endpoint — they lock in the shape of the seed data
(multiple tours, each with multiple concerts, realistic pricing/capacity)
that future dashboard work will build on.
"""

from datetime import datetime
from decimal import Decimal

from tests.fixtures.dashboard_data import compute_dashboard_stats


def test_fixtures_cover_multiple_tours(multi_concert_tour_fixtures):
    assert len(multi_concert_tour_fixtures) >= 3


def test_each_tour_has_multiple_concerts(multi_concert_tour_fixtures):
    for fixture in multi_concert_tour_fixtures:
        assert len(fixture["concerts"]) >= 3


def test_concert_dates_are_in_the_future(multi_concert_tour_fixtures):
    now = datetime.now()
    for fixture in multi_concert_tour_fixtures:
        for concert in fixture["concerts"]:
            assert concert["date_time"] > now


def test_seeded_tours_persist_via_api(client, seeded_multi_concert_tours):
    assert len(seeded_multi_concert_tours) >= 3
    for entry in seeded_multi_concert_tours:
        response = client.get(f"/api/v1/tours/{entry['tour_id']}")
        assert response.status_code == 200


def test_seeded_concerts_are_valid_and_linked_to_their_tour(seeded_multi_concert_tours):
    for entry in seeded_multi_concert_tours:
        for concert in entry["concerts"]:
            assert concert.tour_id == entry["tour_id"]
            assert concert.capacity > 0
            assert concert.ticket_price >= Decimal("0")


def test_dashboard_stats_reflect_seed_data(seeded_multi_concert_tours):
    stats = compute_dashboard_stats(seeded_multi_concert_tours)
    assert stats["total_tours"] == len(seeded_multi_concert_tours)

    expected_total_concerts = sum(len(e["concerts"]) for e in seeded_multi_concert_tours)
    assert stats["total_concerts"] == expected_total_concerts
    assert stats["total_capacity"] > 0
    assert stats["projected_revenue"] > 0
    assert len(stats["countries"]) >= 3
