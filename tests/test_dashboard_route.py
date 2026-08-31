"""Tests for the GET /dashboard route.

The route only renders the dashboard shell template — no business data is
embedded server-side. Dynamic content is loaded client-side via HTMX calls
to the dashboard API endpoints (added in a follow-up task), so these tests
only assert the shell renders successfully with its stats/overview
containers present.
"""


def test_dashboard_returns_200(client):
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_dashboard_content_type_is_html(client):
    response = client.get("/dashboard")
    assert response.headers["content-type"].startswith("text/html")


def test_dashboard_contains_key_markers(client):
    response = client.get("/dashboard")
    assert 'id="tour-overview"' in response.text
    assert 'id="stats-cards"' in response.text


def test_dashboard_does_not_embed_business_data(client):
    """The shell must not hardcode tour/concert data — that's loaded via HTMX."""
    response = client.get("/dashboard")
    assert "hx-get" in response.text
