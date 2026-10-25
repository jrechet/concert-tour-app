"""
Tests for the TourOccupancySchema.
"""

import pytest
from pydantic import ValidationError

from src.schemas import TourOccupancySchema


def test_valid_payload_serialises_with_all_fields():
    schema = TourOccupancySchema(
        tour_id=1,
        tickets_sold=120,
        total_capacity=300,
        percentage_sold=40.0,
    )

    data = schema.dict()

    assert data == {
        "tour_id": 1,
        "tickets_sold": 120,
        "total_capacity": 300,
        "percentage_sold": 40.0,
    }


def test_missing_required_field_raises_validation_error():
    with pytest.raises(ValidationError):
        TourOccupancySchema(tour_id=1, tickets_sold=120, percentage_sold=40.0)


def test_wrong_type_raises_validation_error():
    with pytest.raises(ValidationError):
        TourOccupancySchema(
            tour_id=1,
            tickets_sold="many",
            total_capacity=300,
            percentage_sold=40.0,
        )


def test_zero_capacity_payload_is_accepted():
    schema = TourOccupancySchema(
        tour_id=1,
        tickets_sold=0,
        total_capacity=0,
        percentage_sold=0.0,
    )

    assert schema.total_capacity == 0
    assert schema.percentage_sold == 0.0
