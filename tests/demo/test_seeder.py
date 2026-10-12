"""Tests for `src.demo.seeder`, exercised against a real transactional
database session (the `db_session` fixture from `tests/conftest.py`) so
foreign-key resolution is actually tested, not mocked.
"""

from src.demo import config
from src.demo.seeder import clear_demo, seed_demo
from src.models import Band, Concert, TicketTier, Tour, Venue


def _counts(session):
    return {
        "band": session.query(Band).count(),
        "venue": session.query(Venue).count(),
        "tour": session.query(Tour).count(),
        "concert": session.query(Concert).count(),
        "tier": session.query(TicketTier).count(),
    }


def test_seed_demo_inserts_full_graph(db_session):
    seed_demo(db_session)

    counts = _counts(db_session)
    assert counts["band"] == 1
    assert counts["venue"] == config.DEMO_VENUE_COUNT
    assert counts["tour"] == 1
    assert counts["concert"] == config.DEMO_VENUE_COUNT
    assert counts["tier"] == config.DEMO_VENUE_COUNT * len(config.DEMO_TICKET_TIER_NAMES)

    tour_ids = {row.id for row in db_session.query(Tour.id)}
    venue_ids = {row.id for row in db_session.query(Venue.id)}
    for concert in db_session.query(Concert):
        assert concert.tour_id in tour_ids
        assert concert.venue_id in venue_ids


def test_seed_demo_is_idempotent(db_session):
    seed_demo(db_session)
    before = _counts(db_session)

    seed_demo(db_session)

    assert _counts(db_session) == before


def test_seed_demo_reset_replaces_rows(db_session):
    seed_demo(db_session)
    before = _counts(db_session)

    tour = db_session.query(Tour).filter_by(name=config.DEMO_TOUR_NAME).one()
    tour.status = "mutated-by-test"
    db_session.flush()

    seed_demo(db_session, reset=True)

    assert _counts(db_session) == before
    refreshed_tour = db_session.query(Tour).filter_by(name=config.DEMO_TOUR_NAME).one()
    assert refreshed_tour.status != "mutated-by-test"


def test_clear_demo_leaves_non_demo_rows(db_session):
    seed_demo(db_session)
    non_demo_band = Band(name="Totally Different Band")
    non_demo_venue = Venue(name="Local Dive Bar", city="Smalltown", country="USA", capacity=100)
    db_session.add_all([non_demo_band, non_demo_venue])
    db_session.flush()

    clear_demo(db_session)

    assert _counts(db_session) == {"band": 1, "venue": 1, "tour": 0, "concert": 0, "tier": 0}
    assert db_session.query(Band).filter_by(name="Totally Different Band").one_or_none() is not None
    assert db_session.query(Venue).filter_by(name="Local Dive Bar").one_or_none() is not None
