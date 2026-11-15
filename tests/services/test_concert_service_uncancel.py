"""Unit tests for `uncancel_concert`, independent of the HTTP layer."""

from datetime import datetime

import pytest
from sqlalchemy import event as sa_event

from src.models import ConcertStatus
from src.services.concert_service import (
    ConcertNotCancelledError,
    ConcertPastDateError,
    uncancel_concert,
)
from src.services.concerts_service import ConcertNotFoundError
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _create_concert(db_session, day_offset, status):
    """Persist a concert on its own real tour/venue, with `status` set
    directly (the fixture itself only models `is_cancelled`)."""
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    concert = create_concert(
        db_session, tour, venue, day_offset=day_offset, ticket_price="80.00", base_time=BASE_TIME,
    )
    concert.status = status
    db_session.commit()
    db_session.refresh(concert)
    return concert


def _track_commits(db_session):
    commits = []
    sa_event.listen(db_session, "after_commit", lambda session: commits.append(session))
    return commits


class TestUncancelConcert:
    """Coverage for `uncancel_concert`."""

    def test_restores_cancelled_future_concert_and_persists_status(self, db_session, monkeypatch):
        concert = _create_concert(db_session, day_offset=5, status=ConcertStatus.cancelled)
        monkeypatch.setattr("src.services.concert_service.get_reference_time", lambda: BASE_TIME)

        result = uncancel_concert(db_session, concert.id)

        assert result.id == concert.id
        assert result.status == ConcertStatus.scheduled

        db_session.refresh(concert)
        assert concert.status == ConcertStatus.scheduled

    def test_unknown_concert_id_raises_not_found_without_writing(self, db_session):
        commits = _track_commits(db_session)

        with pytest.raises(ConcertNotFoundError):
            uncancel_concert(db_session, 999)

        assert commits == []

    def test_already_scheduled_concert_raises_not_cancelled_without_writing(self, db_session):
        concert = _create_concert(db_session, day_offset=5, status=ConcertStatus.scheduled)
        commits = _track_commits(db_session)

        with pytest.raises(ConcertNotCancelledError, match="scheduled"):
            uncancel_concert(db_session, concert.id)

        assert commits == []
        db_session.refresh(concert)
        assert concert.status == ConcertStatus.scheduled

    def test_cancelled_but_past_dated_concert_raises_past_date_without_writing(self, db_session):
        concert = _create_concert(db_session, day_offset=-5, status=ConcertStatus.cancelled)
        commits = _track_commits(db_session)

        with pytest.raises(ConcertPastDateError):
            uncancel_concert(db_session, concert.id)

        assert commits == []
        db_session.refresh(concert)
        assert concert.status == ConcertStatus.cancelled

    def test_non_cancelled_and_past_dated_concert_raises_not_cancelled_deterministically(self, db_session):
        concert = _create_concert(db_session, day_offset=-5, status=ConcertStatus.scheduled)
        commits = _track_commits(db_session)

        with pytest.raises(ConcertNotCancelledError):
            uncancel_concert(db_session, concert.id)

        assert commits == []

    def test_defaults_reference_time_to_get_reference_time(self, db_session, monkeypatch):
        concert = _create_concert(db_session, day_offset=-1, status=ConcertStatus.cancelled)

        monkeypatch.setattr("src.services.concert_service.get_reference_time", lambda: BASE_TIME)

        with pytest.raises(ConcertPastDateError):
            uncancel_concert(db_session, concert.id)
