"""Unit tests for the `TicketPurchaseRequest` schema, independent of the
HTTP layer.
"""

import pytest
from pydantic import ValidationError

from src.schemas.ticket import TicketPurchaseRequest


def test_valid_quantity_is_accepted():
    request = TicketPurchaseRequest(quantity=2)

    assert request.quantity == 2


def test_quantity_of_one_is_accepted():
    request = TicketPurchaseRequest(quantity=1)

    assert request.quantity == 1


def test_quantity_zero_raises_validation_error():
    with pytest.raises(ValidationError):
        TicketPurchaseRequest(quantity=0)


def test_negative_quantity_raises_validation_error():
    with pytest.raises(ValidationError):
        TicketPurchaseRequest(quantity=-1)


def test_non_integer_quantity_raises_validation_error():
    with pytest.raises(ValidationError):
        TicketPurchaseRequest(quantity="not-a-number")


def test_float_quantity_with_fractional_part_raises_validation_error():
    with pytest.raises(ValidationError):
        TicketPurchaseRequest(quantity=1.5)


def test_missing_quantity_raises_validation_error():
    with pytest.raises(ValidationError):
        TicketPurchaseRequest()
