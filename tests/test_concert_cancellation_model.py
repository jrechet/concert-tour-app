"""Model-level tests for Concert cancellation validation.

Complements tests/test_concerts_cancellation.py (API-level cancel/uncancel
behavior) by exercising the invariant directly on the SQLAlchemy model:
a cancelled concert must always carry a non-empty reason, and an active
concert must never carry a stale one, regardless of the order the two
attributes were set in or whether the change goes through `flush()` or
`commit()`.
"""

import pytest
from datetime import datetime, timedelta

from src.models import Concert, Tour, Venue


def _seed_tour_and_venue(db_session):
    tour = Tour(
        name="Cancellation Model Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = Venue(name="Test Arena", city="Testville", country="USA", capacity=1000)
    db_session.add_all([tour, venue])
    db_session.commit()
    db_session.refresh(tour)
    db_session.refresh(venue)
    return tour, venue


def _make_concert(tour, venue, **kwargs):
    return Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=datetime.now() + timedelta(days=5),
        **kwargs,
    )


class TestCancellationRequiresReason:
    def test_cancelled_with_no_reason_raises_on_insert(self, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = _make_concert(tour, venue, is_cancelled=True)

        db_session.add(concert)
        with pytest.raises(ValueError):
            db_session.commit()

    def test_cancelled_with_empty_reason_raises_on_insert(self, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = _make_concert(tour, venue, is_cancelled=True, cancellation_reason="   ")

        db_session.add(concert)
        with pytest.raises(ValueError):
            db_session.commit()

    def test_cancelled_with_valid_reason_persists(self, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = _make_concert(tour, venue, is_cancelled=True, cancellation_reason="Artist illness")

        db_session.add(concert)
        db_session.commit()
        db_session.refresh(concert)

        assert concert.is_cancelled is True
        assert concert.cancellation_reason == "Artist illness"

    def test_cancelling_existing_concert_with_no_reason_raises_on_update(self, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = _make_concert(tour, venue)
        db_session.add(concert)
        db_session.commit()

        concert.is_cancelled = True
        with pytest.raises(ValueError):
            db_session.commit()


class TestUncancellingClearsReason:
    def test_not_cancelled_forces_reason_to_none_on_insert(self, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = _make_concert(tour, venue, is_cancelled=False, cancellation_reason="Stale reason")

        db_session.add(concert)
        db_session.commit()
        db_session.refresh(concert)

        assert concert.is_cancelled is False
        assert concert.cancellation_reason is None

    def test_uncancelling_clears_previously_set_reason(self, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = _make_concert(tour, venue, is_cancelled=True, cancellation_reason="Weather")
        db_session.add(concert)
        db_session.commit()

        concert.is_cancelled = False
        db_session.commit()
        db_session.refresh(concert)

        assert concert.is_cancelled is False
        assert concert.cancellation_reason is None
