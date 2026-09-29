"""
Unit tests for CancelTour Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.schemas.tour import CancelTourRequest, CancelTourResponse, TourCitiesResponse


class TestCancelTourRequest:
    """Test cases for CancelTourRequest schema."""

    def test_valid_payload(self):
        request = CancelTourRequest(reason="Artist illness")
        assert request.reason == "Artist illness"

    def test_missing_reason_raises(self):
        with pytest.raises(ValidationError):
            CancelTourRequest()

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError):
            CancelTourRequest(reason="")

    def test_whitespace_only_reason_raises(self):
        with pytest.raises(ValidationError):
            CancelTourRequest(reason="   ")

    def test_reason_is_trimmed(self):
        request = CancelTourRequest(reason="  Weather conditions  ")
        assert request.reason == "Weather conditions"


class TestCancelTourResponse:
    """Test cases for CancelTourResponse schema."""

    def test_valid_payload(self):
        response = CancelTourResponse(cancelled_count=5)
        assert response.cancelled_count == 5

    def test_missing_cancelled_count_raises(self):
        with pytest.raises(ValidationError):
            CancelTourResponse()


class TestTourCitiesResponse:
    """Test cases for TourCitiesResponse schema."""

    def test_valid_payload(self):
        response = TourCitiesResponse(tour_id=1, cities=["New York", "London"])
        assert response.tour_id == 1
        assert response.cities == ["New York", "London"]

    def test_empty_cities_list_is_valid(self):
        response = TourCitiesResponse(tour_id=1, cities=[])
        assert response.cities == []

    def test_missing_tour_id_raises(self):
        with pytest.raises(ValidationError):
            TourCitiesResponse(cities=["New York"])

    def test_missing_cities_raises(self):
        with pytest.raises(ValidationError):
            TourCitiesResponse(tour_id=1)
