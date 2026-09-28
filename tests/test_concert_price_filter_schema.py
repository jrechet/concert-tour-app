"""Unit tests for the `ConcertPriceFilter` query-parameter schema itself,
independent of the HTTP layer.
"""

import pytest
from pydantic import ValidationError

from src.schemas.concert import ConcertPriceFilter


def test_both_none_is_valid():
    price_filter = ConcertPriceFilter()

    assert price_filter.min_price is None
    assert price_filter.max_price is None


def test_min_price_below_max_price_is_valid():
    price_filter = ConcertPriceFilter(min_price=10, max_price=50)

    assert price_filter.min_price == 10
    assert price_filter.max_price == 50


def test_min_price_equal_to_max_price_is_valid():
    price_filter = ConcertPriceFilter(min_price=25, max_price=25)

    assert price_filter.min_price == price_filter.max_price == 25


def test_min_price_above_max_price_raises_validation_error():
    with pytest.raises(ValidationError, match="min_price must not be greater than max_price"):
        ConcertPriceFilter(min_price=50, max_price=10)


def test_negative_min_price_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertPriceFilter(min_price=-1)


def test_negative_max_price_raises_validation_error():
    with pytest.raises(ValidationError):
        ConcertPriceFilter(max_price=-1)
