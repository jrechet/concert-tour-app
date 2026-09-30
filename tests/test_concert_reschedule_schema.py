"""Unit tests for the `ConcertRescheduleRequest` schema, independent of the HTTP layer."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas.concert import ConcertRescheduleRequest


def test_valid_date_time_is_accepted():
    request = ConcertRescheduleRequest(date_time="2024-08-01T20:00:00")

    assert request.date_time == datetime(2024, 8, 1, 20, 0, 0)


def test_missing_date_time_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertRescheduleRequest()


def test_invalid_date_time_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertRescheduleRequest(date_time="not-a-date")
