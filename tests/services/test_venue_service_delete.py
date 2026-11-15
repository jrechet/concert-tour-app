"""Unit tests for `delete_venue`."""

from datetime import datetime, timedelta

import pytest

from src.models import Venue
from src.services.venue_service import (
    VenueHasConcertsError,
    VenueNotFoundError,
    delete_venue,
)
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2026, 6, 1, 12, 0, 0)


def _make_tour(db_session):
    """Persist and return a `Tour` row spanning `REFERENCE_TIME`."""
    return create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (REFERENCE_TIME - timedelta(days=60)).date(),
        (REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )


class TestDeleteVenue:
    """Coverage for `delete_venue`."""

    def test_deletes_venue_with_no_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        venue_id = venue.id

        delete_venue(db_session, venue_id)

        assert db_session.query(Venue).filter(Venue.id == venue_id).first() is None

    def test_raises_conflict_with_count_one_and_leaves_venue_untouched(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)
        create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        with pytest.raises(VenueHasConcertsError) as exc_info:
            delete_venue(db_session, venue.id)

        assert exc_info.value.concert_count == 1
        assert db_session.query(Venue).filter(Venue.id == venue.id).first() is not None

    def test_raises_conflict_with_count_matching_several_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)
        for day_offset in (5, 10, 15):
            create_concert(
                db_session, tour, venue, day_offset=day_offset, ticket_price="50.00",
                base_time=REFERENCE_TIME,
            )

        with pytest.raises(VenueHasConcertsError) as exc_info:
            delete_venue(db_session, venue.id)

        assert exc_info.value.concert_count == 3
        assert db_session.query(Venue).filter(Venue.id == venue.id).first() is not None

    def test_raises_not_found_for_unknown_venue_id_and_commits_nothing(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        unknown_venue_id = venue.id + 1

        while db_session.query(Venue).filter(Venue.id == unknown_venue_id).first() is not None:
            unknown_venue_id += 1

        with pytest.raises(VenueNotFoundError):
            delete_venue(db_session, unknown_venue_id)

        assert db_session.query(Venue).filter(Venue.id == venue.id).first() is not None
