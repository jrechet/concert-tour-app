"""
Unit tests for CancelTour Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.schemas.tour import CancelTourRequest, CancelTourResponse


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
