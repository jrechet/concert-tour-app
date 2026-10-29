"""Unit tests for the `ConcertDateRangeQuery` query-parameter schema used by
`GET /api/v1/concerts/between`, independent of the HTTP layer.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.schemas.concert import ConcertDateRangeQuery


def test_valid_range_parses_to_date_objects():
    query = ConcertDateRangeQuery(start="2026-01-01", end="2026-12-31")

    assert query.start == date(2026, 1, 1)
    assert query.end == date(2026, 12, 31)


def test_start_equal_to_end_is_valid():
    query = ConcertDateRangeQuery(start="2026-06-15", end="2026-06-15")

    assert query.start == query.end == date(2026, 6, 15)


def test_start_after_end_raises_validation_error():
    with pytest.raises(ValidationError, match="start must be on or before end"):
        ConcertDateRangeQuery(start="2026-06-15", end="2026-06-14")


@pytest.mark.parametrize("malformed_date", ["2026-13-01", "01-02-2026", "not-a-date", ""])
def test_malformed_date_raises_validation_error(malformed_date):
    with pytest.raises(ValidationError):
        ConcertDateRangeQuery(start=malformed_date, end="2026-12-31")


def test_missing_start_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertDateRangeQuery(end="2026-12-31")


def test_missing_end_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertDateRangeQuery(start="2026-01-01")
