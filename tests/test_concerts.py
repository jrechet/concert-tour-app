"""Tests for the concert list/detail JSON API endpoints."""

from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import event

from src.models import Venue
from tests.conftest import engine
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


@contextmanager
def _count_queries():
    """Count SQL statements executed against the test engine while the
    `with` block runs, so tests can assert a fixed query count rather than
    one that scales with the number of rows returned (i.e. no N+1)."""
    statements = []

    def _listener(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _listener)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", _listener)


def _seed_tour_and_venue(db_session):
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return tour, venue


def _seed_multi_city_tour(db_session, venue_count=3, name="Multi-City E2E Tour"):
    """A single tour with `venue_count` distinct-city venues, real FKs throughout."""
    tour = create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=venue_count)
    return tour, venues


def _seed_tour_with_artist(db_session, artist, name=None):
    """A tour (with its own dedicated venue) for a specific artist, real FKs throughout."""
    tour = create_tour(
        db_session,
        name=name or f"{artist} Tour",
        artist=artist,
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return tour, venue


def test_get_concerts_includes_remaining_tickets_and_sold_out(client, db_session):
    """Every concert in the list response carries the derived fields."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=100,
    )

    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["remaining_tickets"] == venue.capacity - 100
    assert data[0]["sold_out"] is False
    assert data[0]["tickets_sold"] == 100


def test_get_concerts_sold_out_when_zero_remaining(client, db_session):
    """A concert with tickets_sold == venue capacity reports sold_out."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/api/v1/concerts/")
    data = response.json()[0]
    assert data["remaining_tickets"] == 0
    assert data["sold_out"] is True


def test_get_concerts_pagination(client, db_session):
    """skip/limit continue to page results with the added fields present."""
    tour, venue = _seed_tour_and_venue(db_session)
    base_time = datetime.now()
    for i in range(5):
        create_concert(
            db_session, tour, venue, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=i,
        )

    response = client.get("/api/v1/concerts/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for concert in data:
        assert "remaining_tickets" in concert
        assert "sold_out" in concert


def test_get_concerts_empty(client):
    """An empty database returns an empty list, not an error."""
    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_concert_by_id(client, db_session):
    """Fetching a single concert includes the derived fields too."""
    tour, venue = _seed_tour_and_venue(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get(f"/api/v1/concerts/{concert.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["sold_out"] is True
    assert data["remaining_tickets"] == 0


def test_get_concert_not_found(client):
    """Requesting a nonexistent concert returns 404."""
    response = client.get("/api/v1/concerts/999")
    assert response.status_code == 404


def test_get_concerts_filtered_by_city(client, db_session):
    """?city=<City> narrows results to concerts whose venue is in that city."""
    tour = create_tour(
        db_session,
        name="Multi-City Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=2)  # New York, London
    base_time = datetime.now()
    create_concert(
        db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
        base_time=base_time, tickets_sold=0,
    )
    create_concert(
        db_session, tour, venues[1], day_offset=2, ticket_price="60.00",
        base_time=base_time, tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/?city=New York")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["venue_id"] == venues[0].id


def test_get_concerts_filtered_by_city_case_insensitive(client, db_session):
    """City filtering matches regardless of case."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get(f"/api/v1/concerts/?city={venue.city.upper()}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_concerts_unknown_city_returns_empty_list(client, db_session):
    """An unknown/nonexistent city returns an empty list, not an error."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/?city=Nonexistentville")
    assert response.status_code == 200
    assert response.json() == []


def test_get_concerts_filtered_by_venue(client, db_session):
    """?venue=<Venue> narrows results to concerts at that venue."""
    tour = create_tour(
        db_session,
        name="Multi-Venue Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=2)
    base_time = datetime.now()
    create_concert(
        db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
        base_time=base_time, tickets_sold=0,
    )
    create_concert(
        db_session, tour, venues[1], day_offset=2, ticket_price="60.00",
        base_time=base_time, tickets_sold=0,
    )

    response = client.get(f"/api/v1/concerts/?venue={venues[0].name}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["venue_id"] == venues[0].id


def test_get_concerts_filtered_by_venue_case_insensitive(client, db_session):
    """Venue filtering matches regardless of case."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    exact_response = client.get(f"/api/v1/concerts/?venue={venue.name}")
    upper_response = client.get(f"/api/v1/concerts/?venue={venue.name.upper()}")
    assert exact_response.status_code == 200
    assert upper_response.status_code == 200
    assert exact_response.json() == upper_response.json()
    assert len(upper_response.json()) == 1


def test_get_concerts_unknown_venue_returns_empty_list(client, db_session):
    """An unknown/nonexistent venue returns an empty list, not an error."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/?venue=Nonexistent Arena")
    assert response.status_code == 200
    assert response.json() == []


def test_get_concerts_no_venue_filter_returns_all(client, db_session):
    """Omitting venue returns all concerts, matching existing behavior."""
    tour = create_tour(
        db_session,
        name="Multi-Venue Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=2)
    base_time = datetime.now()
    create_concert(
        db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
        base_time=base_time, tickets_sold=0,
    )
    create_concert(
        db_session, tour, venues[1], day_offset=2, ticket_price="60.00",
        base_time=base_time, tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_concerts_city_filter_combines_with_pagination(client, db_session):
    """city filter and skip/limit combine correctly."""
    tour = create_tour(
        db_session,
        name="Repeat City Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=1)
    venue = venues[0]
    base_time = datetime.now()
    for i in range(5):
        create_concert(
            db_session, tour, venue, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=i,
        )

    response = client.get(f"/api/v1/concerts/?city={venue.city}&skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for concert in data:
        assert concert["venue_id"] == venue.id


class TestCityFilterEndToEnd:
    """End-to-end coverage for the city filter: multi-city pagination
    interaction and the full apply/clear user flow, on top of the isolated
    single-scenario tests above."""

    def test_filter_by_valid_city_narrows_results(self, client, db_session):
        """Filtering by one of several distinct cities returns only that
        city's concerts."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        target = venues[1]
        response = client.get(f"/api/v1/concerts/?city={target.city}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == target.id

    def test_filter_by_city_with_no_matches_returns_empty(self, client, db_session):
        tour, venues = _seed_multi_city_tour(db_session, venue_count=2)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        response = client.get("/api/v1/concerts/?city=Atlantis")
        assert response.status_code == 200
        assert response.json() == []

    def test_no_filter_returns_concerts_across_all_cities(self, client, db_session):
        """With no `city` param, concerts from every city are returned."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(venues)
        assert {c["venue_id"] for c in data} == {v.id for v in venues}

    def test_filter_then_clear_returns_to_unfiltered_state(self, client, db_session):
        """Full user flow: load the unfiltered list (as a UI would to
        populate a city picker), apply a city filter, then clear it and
        confirm the list matches what was originally loaded."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        baseline_response = client.get("/api/v1/concerts/")
        assert baseline_response.status_code == 200
        baseline = baseline_response.json()
        assert len(baseline) == 3

        filtered_response = client.get(f"/api/v1/concerts/?city={venues[0].city}")
        assert filtered_response.status_code == 200
        filtered = filtered_response.json()
        assert len(filtered) == 1
        assert filtered[0]["venue_id"] == venues[0].id

        cleared_response = client.get("/api/v1/concerts/")
        assert cleared_response.status_code == 200
        assert cleared_response.json() == baseline

    def test_filter_combined_with_pagination_uses_filtered_subset(self, client, db_session):
        """skip/limit must apply to the filtered result set, not the
        unfiltered total, confirming the filter is applied before
        pagination."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=2)
        target, other = venues
        base_time = datetime.now()
        for i in range(3):
            create_concert(
                db_session, tour, target, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )
        for i in range(5):
            create_concert(
                db_session, tour, other, day_offset=10 + i, ticket_price="60.00",
                base_time=base_time, tickets_sold=0,
            )

        # 8 concerts total, but only 3 belong to `target`. skip=2, limit=5
        # against the filtered subset should yield exactly 1 result.
        response = client.get(f"/api/v1/concerts/?city={target.city}&skip=2&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == target.id

    def test_filter_combined_with_pagination_skip_beyond_filtered_count_is_empty(self, client, db_session):
        """skip past the end of the filtered subset returns an empty list,
        even though unfiltered data exists further along."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=2)
        target, other = venues
        base_time = datetime.now()
        for i in range(3):
            create_concert(
                db_session, tour, target, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )
        for i in range(5):
            create_concert(
                db_session, tour, other, day_offset=10 + i, ticket_price="60.00",
                base_time=base_time, tickets_sold=0,
            )

        response = client.get(f"/api/v1/concerts/?city={target.city}&skip=3&limit=5")
        assert response.status_code == 200
        assert response.json() == []


class TestCityFilterSqlSafetyAndEdgeCases:
    """Coverage for city values containing characters with special meaning
    in SQL LIKE patterns (`%`, `_`) or string literals (quotes), and for
    mixed-case multi-word city names, confirming the filter is
    parameterized and treats these values as plain literals rather than
    interpreting them as SQL syntax."""

    def test_mixed_case_multi_word_city_matches(self, client, db_session):
        """A mixed-case, all-lowercase query for a multi-word city name
        ("New York") still matches."""
        tour, venue = _seed_tour_and_venue(db_session)  # venue.city == "New York"
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/", params={"city": "new york"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == venue.id

    def test_city_filter_treats_percent_character_as_literal(self, client, db_session):
        """A city value containing `%` is matched literally, not as a SQL
        LIKE wildcard that would incorrectly also match unrelated cities."""
        tour = create_tour(
            db_session, name="Percent City Tour", artist="Test Artist",
            start_date=(datetime.now() - timedelta(days=1)).date(),
            end_date=(datetime.now() + timedelta(days=90)).date(),
            status="active",
        )
        percent_venue = Venue(name="Percent Arena", city="50% City", country="USA", capacity=5000)
        other_venue = Venue(name="Other Arena", city="50X City", country="USA", capacity=5000)
        db_session.add_all([percent_venue, other_venue])
        db_session.commit()
        db_session.refresh(percent_venue)
        db_session.refresh(other_venue)
        base_time = datetime.now()
        create_concert(
            db_session, tour, percent_venue, day_offset=1, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )
        create_concert(
            db_session, tour, other_venue, day_offset=2, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/", params={"city": "50% City"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == percent_venue.id

    def test_city_filter_treats_underscore_character_as_literal(self, client, db_session):
        """A city value containing `_` is matched literally, not as a SQL
        LIKE single-character wildcard that would incorrectly also match
        unrelated cities."""
        tour = create_tour(
            db_session, name="Underscore City Tour", artist="Test Artist",
            start_date=(datetime.now() - timedelta(days=1)).date(),
            end_date=(datetime.now() + timedelta(days=90)).date(),
            status="active",
        )
        underscore_venue = Venue(name="Underscore Arena", city="Spring_field", country="USA", capacity=5000)
        other_venue = Venue(name="Other Arena", city="SpringXfield", country="USA", capacity=5000)
        db_session.add_all([underscore_venue, other_venue])
        db_session.commit()
        db_session.refresh(underscore_venue)
        db_session.refresh(other_venue)
        base_time = datetime.now()
        create_concert(
            db_session, tour, underscore_venue, day_offset=1, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )
        create_concert(
            db_session, tour, other_venue, day_offset=2, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/", params={"city": "Spring_field"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == underscore_venue.id

    def test_city_filter_matches_partial_substring(self, client, db_session):
        """A query for a substring of a city name (not the full name) still
        matches, e.g. "paris" matching a venue city of "Paris, France"."""
        tour = create_tour(
            db_session, name="Partial Match Tour", artist="Test Artist",
            start_date=(datetime.now() - timedelta(days=1)).date(),
            end_date=(datetime.now() + timedelta(days=90)).date(),
            status="active",
        )
        paris_venue = Venue(name="Paris Arena", city="Paris, France", country="France", capacity=5000)
        other_venue = Venue(name="Other Arena", city="London", country="UK", capacity=5000)
        db_session.add_all([paris_venue, other_venue])
        db_session.commit()
        db_session.refresh(paris_venue)
        db_session.refresh(other_venue)
        base_time = datetime.now()
        create_concert(
            db_session, tour, paris_venue, day_offset=1, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )
        create_concert(
            db_session, tour, other_venue, day_offset=2, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/", params={"city": "paris"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == paris_venue.id

    def test_city_filter_blank_value_returns_unfiltered_list(self, client, db_session):
        """An empty `city` query param is treated the same as omitting the
        filter, returning the full unfiltered list."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        response = client.get("/api/v1/concerts/", params={"city": ""})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(venues)

    def test_city_filter_handles_quote_character_without_error(self, client, db_session):
        """A city value containing a single quote is handled safely by the
        parameterized query rather than raising a database error."""
        tour, _ = _seed_tour_and_venue(db_session)
        quote_venue = Venue(name="O'Fallon Arena", city="O'Fallon", country="USA", capacity=5000)
        db_session.add(quote_venue)
        db_session.commit()
        db_session.refresh(quote_venue)
        create_concert(
            db_session, tour, quote_venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/", params={"city": "O'Fallon"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == quote_venue.id

    def test_city_filter_sql_injection_payload_returns_empty_not_error(self, client, db_session):
        """A classic SQL-injection payload in `city` is treated as a plain
        (non-matching) string value: a 200 with an empty list, never a
        database error and never an unintended full-table match."""
        tour, venue = _seed_tour_and_venue(db_session)
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/", params={"city": "' OR '1'='1"})
        assert response.status_code == 200
        assert response.json() == []


class TestArtistNameFilterEndToEnd:
    """Coverage for the `artist_name` filter on the concerts list endpoint:
    exact/mixed-case matching, partial substring matching, no-match empty
    results, and interaction with pagination."""

    def test_exact_case_match_returns_expected_concerts(self, client, db_session):
        """An exact-case artist_name query returns only that artist's concerts."""
        tour, venue = _seed_tour_with_artist(db_session, "Aurora Belle")
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )
        other_tour, other_venue = _seed_tour_with_artist(db_session, "River Stone")
        create_concert(
            db_session, other_tour, other_venue, day_offset=2, ticket_price="60.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/?artist_name=Aurora Belle")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["tour_id"] == tour.id

    def test_mixed_case_query_matches_case_insensitively(self, client, db_session):
        """A query in the opposite/mixed case still matches the artist."""
        tour, venue = _seed_tour_with_artist(db_session, "Aurora Belle")
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/?artist_name=aURORA bELLE")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["tour_id"] == tour.id

    def test_partial_substring_query_matches(self, client, db_session):
        """A substring of the artist name matches concerts for that artist."""
        tour, venue = _seed_tour_with_artist(db_session, "The Midnight Collective")
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )
        other_tour, other_venue = _seed_tour_with_artist(db_session, "River Stone")
        create_concert(
            db_session, other_tour, other_venue, day_offset=2, ticket_price="60.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/?artist_name=Midnight")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["tour_id"] == tour.id

    def test_query_with_no_matches_returns_empty_list(self, client, db_session):
        """An artist name with no matches returns an empty list, not an error."""
        tour, venue = _seed_tour_with_artist(db_session, "Aurora Belle")
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        response = client.get("/api/v1/concerts/?artist_name=Nonexistent Artist")
        assert response.status_code == 200
        assert response.json() == []

    def test_filter_combined_with_pagination_uses_filtered_subset(self, client, db_session):
        """skip/limit apply to the artist_name-filtered subset, not the
        unfiltered total."""
        tour, venue = _seed_tour_with_artist(db_session, "Aurora Belle")
        base_time = datetime.now()
        for i in range(3):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )
        other_tour, other_venue = _seed_tour_with_artist(db_session, "River Stone")
        for i in range(5):
            create_concert(
                db_session, other_tour, other_venue, day_offset=10 + i, ticket_price="60.00",
                base_time=base_time, tickets_sold=0,
            )

        # 8 concerts total, but only 3 belong to "Aurora Belle". skip=1,
        # limit=5 against the filtered subset should yield exactly 2 results,
        # and the total filtered count (checked via an unpaginated request)
        # should be exactly 3.
        unpaginated = client.get("/api/v1/concerts/?artist_name=Aurora Belle")
        assert unpaginated.status_code == 200
        assert len(unpaginated.json()) == 3

        response = client.get("/api/v1/concerts/?artist_name=Aurora Belle&skip=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for concert in data:
            assert concert["tour_id"] == tour.id


class TestRemainingTicketsField:
    """Dedicated coverage for `remaining_tickets`: no sales, partial sales,
    fully sold out, and the oversold clamp-to-zero edge case, verified on
    both the detail endpoint and across a paginated list."""

    def test_no_tickets_sold_remaining_equals_capacity(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        detail = client.get(f"/api/v1/concerts/{concert.id}")
        assert detail.status_code == 200
        assert detail.json()["remaining_tickets"] == venue.capacity
        assert detail.json()["sold_out"] is False

        listing = client.get("/api/v1/concerts/")
        assert listing.json()[0]["remaining_tickets"] == venue.capacity

    def test_partial_sales_remaining_is_capacity_minus_sold(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        sold = venue.capacity // 3
        concert = create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=sold,
        )

        detail = client.get(f"/api/v1/concerts/{concert.id}")
        assert detail.json()["remaining_tickets"] == venue.capacity - sold
        assert detail.json()["sold_out"] is False

        listing = client.get("/api/v1/concerts/")
        assert listing.json()[0]["remaining_tickets"] == venue.capacity - sold

    def test_fully_sold_out_remaining_is_zero(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=venue.capacity,
        )

        detail = client.get(f"/api/v1/concerts/{concert.id}")
        assert detail.json()["remaining_tickets"] == 0
        assert detail.json()["sold_out"] is True

        listing = client.get("/api/v1/concerts/")
        assert listing.json()[0]["remaining_tickets"] == 0
        assert listing.json()[0]["sold_out"] is True

    def test_oversold_remaining_clamps_to_zero_not_negative(self, client, db_session):
        """tickets_sold can end up above capacity (e.g. a venue's listed
        capacity is revised down after tickets were already sold).
        remaining_tickets must clamp to 0 rather than reporting a negative
        count."""
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=venue.capacity + 250,
        )

        detail = client.get(f"/api/v1/concerts/{concert.id}")
        assert detail.status_code == 200
        assert detail.json()["remaining_tickets"] == 0
        assert detail.json()["sold_out"] is True

        listing = client.get("/api/v1/concerts/")
        assert listing.json()[0]["remaining_tickets"] == 0

    def test_zero_capacity_venue_reports_sold_out_true(self, client, db_session):
        """A venue with zero capacity has zero remaining tickets by
        definition, so `sold_out` must be True on both the list and detail
        endpoints even though no tickets were ever sold."""
        tour = create_tour(
            db_session, name="Zero Capacity Tour", artist="Test Artist",
            start_date=(datetime.now() - timedelta(days=1)).date(),
            end_date=(datetime.now() + timedelta(days=90)).date(),
            status="active",
        )
        venue = Venue(name="Unbuilt Venue", city="Testville", country="USA", capacity=0)
        db_session.add(venue)
        db_session.commit()
        db_session.refresh(venue)
        concert = create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=0,
        )

        detail = client.get(f"/api/v1/concerts/{concert.id}")
        assert detail.status_code == 200
        assert detail.json()["remaining_tickets"] == 0
        assert detail.json()["sold_out"] is True

        listing = client.get("/api/v1/concerts/")
        assert listing.status_code == 200
        assert listing.json()[0]["remaining_tickets"] == 0
        assert listing.json()[0]["sold_out"] is True

    def test_remaining_tickets_correct_per_item_across_paginated_list(self, client, db_session):
        """Each page of results carries the correct remaining_tickets for
        its own concert, not just a presence check."""
        tour, venue = _seed_tour_and_venue(db_session)
        base_time = datetime.now()
        sold_counts = [0, 10, venue.capacity, venue.capacity + 100]
        for i, sold in enumerate(sold_counts):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=sold,
            )

        expected = [venue.capacity, venue.capacity - 10, 0, 0]

        first_page = client.get("/api/v1/concerts/?skip=0&limit=2")
        assert first_page.status_code == 200
        assert [c["remaining_tickets"] for c in first_page.json()] == expected[:2]

        second_page = client.get("/api/v1/concerts/?skip=2&limit=2")
        assert second_page.status_code == 200
        assert [c["remaining_tickets"] for c in second_page.json()] == expected[2:]


class TestRemainingTicketsQueryEfficiency:
    """remaining_tickets is derived from each concert's venue, so the list
    endpoint must eager-load venues in one join rather than issuing a
    separate query per concert (N+1)."""

    def test_list_endpoint_query_count_does_not_scale_with_result_size(self, client, db_session):
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i in range(9):
            create_concert(
                db_session, tour, venues[i % len(venues)], day_offset=i,
                ticket_price="50.00", base_time=base_time, tickets_sold=i,
            )

        with _count_queries() as few_result_queries:
            response = client.get("/api/v1/concerts/?limit=3")
        assert response.status_code == 200
        assert len(response.json()) == 3

        with _count_queries() as many_result_queries:
            response = client.get("/api/v1/concerts/?limit=9")
        assert response.status_code == 200
        assert len(response.json()) == 9

        assert len(few_result_queries) == len(many_result_queries)
        assert len(many_result_queries) == 1

    def test_detail_endpoint_uses_single_query(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=10,
        )

        with _count_queries() as queries:
            response = client.get(f"/api/v1/concerts/{concert.id}")
        assert response.status_code == 200
        assert len(queries) == 1
