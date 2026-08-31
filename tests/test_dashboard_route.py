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


def test_dashboard_contains_calendar_grid_shell(client):
    response = client.get("/dashboard")
    assert 'id="calendar-grid"' in response.text


def test_dashboard_contains_stat_card_placeholders(client):
    response = client.get("/dashboard")
    for stat_id in ("stat-concerts", "stat-cities", "stat-countries", "stat-capacity", "stat-revenue"):
        assert f'id="{stat_id}"' in response.text


def test_dashboard_quick_actions_do_not_link_to_invented_routes(client):
    """No concert-create or setlist route exists on `main` yet, so the quick
    action buttons must not point at invented URLs — they're rendered
    disabled until those routes exist."""
    response = client.get("/dashboard")
    assert 'id="quick-action-add-concert"' in response.text
    assert 'id="quick-action-view-setlist"' in response.text
    assert 'aria-disabled="true"' in response.text


def test_dashboard_links_dark_theme_stylesheet(client):
    response = client.get("/dashboard")
    assert "dashboard.css" in response.text


def test_dashboard_stylesheet_is_served(client):
    response = client.get("/static/css/dashboard.css")
    assert response.status_code == 200
    assert "--color-bg" in response.text
