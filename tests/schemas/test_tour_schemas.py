"""
Unit tests for CancelTour Pydantic schemas.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.models.tour import Tour
from src.schemas.tour import (
    CancelTourRequest,
    CancelTourResponse,
    TourCancelRequest,
    TourCancelResponse,
    TourCitiesResponse,
    TourCityOut,
    SoldOutTourRead,
    TourSummaryRead,
)


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


class TestTourCancelRequest:
    """Test cases for TourCancelRequest schema."""

    def test_missing_reason_raises(self):
        with pytest.raises(ValidationError):
            TourCancelRequest()

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError):
            TourCancelRequest(reason="")

    def test_whitespace_only_reason_raises(self):
        with pytest.raises(ValidationError):
            TourCancelRequest(reason="   ")

    def test_reason_is_trimmed(self):
        request = TourCancelRequest(reason="  Singer ill  ")
        assert request.reason == "Singer ill"


class TestTourCancelResponse:
    """Test cases for TourCancelResponse schema."""

    def test_valid_payload_serialises_as_expected(self):
        response = TourCancelResponse(tour_id=1, cancelled_count=3)
        assert response.dict() == {"tour_id": 1, "cancelled_count": 3}


class TestTourCitiesResponse:
    """Test cases for TourCitiesResponse schema."""

    def test_valid_payload(self):
        response = TourCitiesResponse(
            tour_id=1,
            cities=[
                {"city": "New York", "first_concert_date": "2024-06-01"},
                {"city": "London", "first_concert_date": "2024-06-05"},
            ],
        )
        assert response.tour_id == 1
        assert [c.city for c in response.cities] == ["New York", "London"]

    def test_empty_cities_list_is_valid(self):
        response = TourCitiesResponse(tour_id=1, cities=[])
        assert response.cities == []

    def test_missing_tour_id_raises(self):
        with pytest.raises(ValidationError):
            TourCitiesResponse(cities=[{"city": "New York", "first_concert_date": "2024-06-01"}])

    def test_missing_cities_raises(self):
        with pytest.raises(ValidationError):
            TourCitiesResponse(tour_id=1)


class TestTourCityOut:
    """Test cases for the `TourCityOut` schema."""

    def test_tour_city_out_from_orm_row(self):
        """Builds from an ORM-like row/tuple object exposing `city` and
        `first_concert_date` attributes, via `from_attributes`."""

        class Row:
            city = "New York"
            first_concert_date = date(2024, 6, 1)

        city_out = TourCityOut.model_validate(Row())
        assert city_out.city == "New York"
        assert city_out.first_concert_date == date(2024, 6, 1)

    def test_tour_cities_response_serializes_empty_list(self):
        response = TourCitiesResponse(tour_id=1, cities=[])
        assert response.model_dump() == {"tour_id": 1, "cities": []}

    def test_tour_city_out_rejects_missing_city(self):
        with pytest.raises(ValidationError):
            TourCityOut(first_concert_date="2024-06-01")


class TestSoldOutTourRead:
    """Test cases for `SoldOutTourRead`, the item schema for
    `GET /api/v1/tours/sold-out`."""

    def test_valid_tour_instance_serialises_expected_fields(self):
        tour = Tour(
            id=1,
            name="World Tour 2024",
            artist="Queen",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 12, 31),
            description="An amazing world tour",
            status="active",
        )

        read = SoldOutTourRead.model_validate(tour)

        assert read.model_dump() == {
            "id": 1,
            "name": "World Tour 2024",
            "start_date": date(2024, 6, 1),
            "end_date": date(2024, 12, 31),
            "status": "active",
        }

    def test_missing_required_field_raises(self):
        tour = Tour(
            id=2,
            artist="Queen",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 12, 31),
        )

        with pytest.raises(ValidationError):
            SoldOutTourRead.model_validate(tour)

    def test_nullable_status_serialises_as_null_not_dropped(self):
        tour = Tour(
            id=3,
            name="Solo Tour",
            artist="Artist",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 2, 1),
            status=None,
        )

        dumped = SoldOutTourRead.model_validate(tour).model_dump()

        assert "status" in dumped
        assert dumped["status"] is None


class TestTourSummaryRead:
    """Test cases for `TourSummaryRead`, the item schema for the
    cancelled-tours listing."""

    def test_valid_from_attributes_object(self):
        """Builds from an ORM-like row/tuple object exposing `id`, `name`,
        `start_date`, and `concert_count` attributes, via `from_attributes`."""

        class Row:
            id = 1
            name = "World Tour 2024"
            start_date = date(2024, 6, 1)
            concert_count = 5

        summary = TourSummaryRead.model_validate(Row())

        assert summary.model_dump() == {
            "id": 1,
            "name": "World Tour 2024",
            "start_date": date(2024, 6, 1),
            "concert_count": 5,
        }

    def test_concert_count_zero_is_valid(self):
        summary = TourSummaryRead(
            id=1, name="Solo Tour", start_date=date(2024, 1, 1), concert_count=0
        )
        assert summary.concert_count == 0

    def test_negative_concert_count_raises(self):
        with pytest.raises(ValidationError):
            TourSummaryRead(
                id=1, name="Solo Tour", start_date=date(2024, 1, 1), concert_count=-1
            )

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            TourSummaryRead(id=1, start_date=date(2024, 1, 1), concert_count=0)
