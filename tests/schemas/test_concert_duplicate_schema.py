"""Unit tests for the `ConcertDuplicateRequest` schema, independent of the HTTP layer."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.schemas import concert as concert_schemas
from src.schemas.concert import ConcertDuplicateRequest


@pytest.fixture
def frozen_now(monkeypatch):
    """Freeze the schema's clock so tests don't depend on real time."""
    frozen = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(concert_schemas, "_now_utc", lambda: frozen)
    return frozen


def test_future_aware_date_time_is_accepted_and_round_trips_unchanged(frozen_now):
    future = frozen_now + timedelta(days=1)

    request = ConcertDuplicateRequest(date_time=future)

    assert request.date_time == future


def test_future_naive_date_time_is_accepted_and_round_trips_unchanged(frozen_now):
    future_naive = frozen_now.replace(tzinfo=None) + timedelta(days=1)

    request = ConcertDuplicateRequest(date_time=future_naive)

    assert request.date_time == future_naive
    assert request.date_time.tzinfo is None


def test_date_time_equal_to_now_is_accepted(frozen_now):
    request = ConcertDuplicateRequest(date_time=frozen_now)

    assert request.date_time == frozen_now


def test_past_aware_date_time_raises_validation_error(frozen_now):
    past = frozen_now - timedelta(days=1)

    with pytest.raises(ValidationError):
        ConcertDuplicateRequest(date_time=past)


def test_past_naive_date_time_raises_validation_error(frozen_now):
    past_naive = frozen_now.replace(tzinfo=None) - timedelta(days=1)

    with pytest.raises(ValidationError):
        ConcertDuplicateRequest(date_time=past_naive)


def test_missing_date_time_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertDuplicateRequest()


def test_non_parseable_date_time_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertDuplicateRequest(date_time="not-a-date")


def test_model_validate_accepts_future_date_time(frozen_now):
    future = frozen_now + timedelta(days=1)

    request = ConcertDuplicateRequest.model_validate({"date_time": future.isoformat()})

    assert request.date_time == future
