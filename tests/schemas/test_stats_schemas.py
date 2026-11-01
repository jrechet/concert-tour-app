"""
Unit tests for the `CityRevenue` Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.stats import CityRevenue


class TestCityRevenue:
    """Test cases for the `CityRevenue` schema."""

    def test_valid_payload_round_trips_through_model_dump(self):
        item = CityRevenue(city="Paris", revenue=1500)
        assert item.model_dump() == {"city": "Paris", "revenue": 1500}

    def test_zero_revenue_is_accepted(self):
        item = CityRevenue(city="Paris", revenue=0)
        assert item.revenue == 0

    def test_none_revenue_raises(self):
        with pytest.raises(ValidationError):
            CityRevenue(city="Paris", revenue=None)

    def test_missing_city_raises(self):
        with pytest.raises(ValidationError):
            CityRevenue(revenue=1500)
