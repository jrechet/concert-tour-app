"""Tests for the band-facing demo walkthrough: `GET /demo` (the full page)
and `GET /demo/concerts` (the HTMX city-filter fragment it swaps in).

The page is read-only: it renders the same aggregated data
`GET /api/v1/demo/tour-overview` serves as JSON, and never writes to the
database. These tests exercise it through the HTTP client only.
"""

from pathlib import Path

import pytest

from src import config
from src.demo.dataset import build_demo_dataset
from src.demo.seeder import seed_demo
from src.models import Tour, Venue

PAGE_ENDPOINT = "/demo"
FRAGMENT_ENDPOINT = "/demo/concerts"

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "templates" / "demo"


@pytest.fixture(autouse=True)
def demo_enabled(monkeypatch):
    """Enable the demo feature flag for every test in this module, except
    the ones that explicitly disable it."""
    monkeypatch.setattr(config, "DEMO_ENABLED", True)


def _seed(db_session):
    seed_demo(db_session)
    db_session.commit()


def test_demo_page_returns_200_and_renders_tour(client, db_session):
    _seed(db_session)
    dataset = build_demo_dataset()

    response = client.get(PAGE_ENDPOINT)

    assert response.status_code == 200
    assert dataset.tour.name in response.text
    for venue in dataset.venues:
        assert venue.city in response.text


def test_demo_page_returns_403_when_disabled(client, db_session, monkeypatch):
    _seed(db_session)
    monkeypatch.setattr(config, "DEMO_ENABLED", False)

    response = client.get(PAGE_ENDPOINT)

    assert response.status_code == 403


def test_demo_page_returns_404_when_not_seeded(client):
    response = client.get(PAGE_ENDPOINT)

    assert response.status_code == 404


def test_htmx_city_filter_returns_fragment(client, db_session):
    _seed(db_session)
    dataset = build_demo_dataset()
    target_city = dataset.venues[0].city

    response = client.get(
        FRAGMENT_ENDPOINT,
        params={"city": target_city},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "<html" not in response.text.lower()
    assert target_city in response.text


def test_stored_content_is_escaped(client, db_session):
    _seed(db_session)
    malicious_name = "<script>alert(1)</script>"

    tour = db_session.query(Tour).filter_by(name=build_demo_dataset().tour.name).one()
    tour.artist = malicious_name
    venue = db_session.query(Venue).first()
    venue.name = malicious_name
    db_session.commit()

    response = client.get(PAGE_ENDPOINT)

    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text


def test_no_unprotected_mutating_htmx_attributes():
    for template_path in (TEMPLATES_DIR / "walkthrough.html", TEMPLATES_DIR / "_concert_list.html"):
        content = template_path.read_text()
        has_mutating_attribute = "hx-post" in content or "hx-delete" in content
        if has_mutating_attribute:
            assert "csrf_token" in content, (
                f"{template_path.name} has a mutating HTMX attribute but no CSRF token field"
            )
        else:
            assert "hx-post" not in content
            assert "hx-delete" not in content
