"""Unit tests for the `ConcertReschedule` schema, independent of the HTTP layer."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.schemas.concert import ConcertReschedule


def test_future_aware_date_time_is_accepted_and_exposed_as_utc():
    future = datetime.now(timezone.utc) + timedelta(days=1)

    reschedule = ConcertReschedule(date_time=future)

    assert reschedule.date_time == future
    assert reschedule.date_time.tzinfo is not None
    assert reschedule.date_time.utcoffset() == timedelta(0)


def test_future_naive_date_time_is_accepted_and_treated_as_utc():
    future_naive = datetime.now() + timedelta(days=1)

    reschedule = ConcertReschedule(date_time=future_naive)

    assert reschedule.date_time.tzinfo is not None
    assert reschedule.date_time.replace(tzinfo=None) == future_naive


def test_past_date_time_raises_validation_error():
    past = datetime.now(timezone.utc) - timedelta(days=1)

    with pytest.raises(ValidationError):
        ConcertReschedule(date_time=past)


def test_date_time_equal_to_now_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertReschedule(date_time=datetime.now(timezone.utc))


def test_missing_date_time_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertReschedule()


def test_unknown_extra_field_raises_validation_error():
    future = datetime.now(timezone.utc) + timedelta(days=1)

    with pytest.raises(ValidationError):
        ConcertReschedule(date_time=future, unexpected="value")
