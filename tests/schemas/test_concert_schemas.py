"""
Unit tests for the ConcertPriceUpdate and ArtistConcertRead Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models import Concert, Tour, Venue
from src.schemas.concert import ArtistConcertRead, ConcertPriceUpdate, NextConcertResponse


class TestConcertPriceUpdate:
    """Test cases for ConcertPriceUpdate schema."""

    def test_price_update_accepts_decimal_string(self):
        update = ConcertPriceUpdate(ticket_price="49.50")
        assert update.ticket_price == Decimal("49.50")

    def test_price_update_rejects_negative_price(self):
        with pytest.raises(ValidationError):
            ConcertPriceUpdate(ticket_price="-1.00")

    def test_price_update_rejects_missing_ticket_price(self):
        with pytest.raises(ValidationError):
            ConcertPriceUpdate()

    def test_price_update_rejects_non_numeric_ticket_price(self):
        with pytest.raises(ValidationError):
            ConcertPriceUpdate(ticket_price="not-a-number")


class TestArtistConcertRead:
    """Test cases for the `ArtistConcertRead` schema."""

    def _build_concert(self, db_session):
        tour = Tour(
            name="World Tour",
            artist="Test Artist",
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date(),
        )
        venue = Venue(name="Wembley Stadium", city="London", country="UK", capacity=90000)
        db_session.add_all([tour, venue])
        db_session.commit()

        concert = Concert(tour_id=tour.id, venue_id=venue.id, date_time=datetime(2024, 7, 15, 20, 0))
        db_session.add(concert)
        db_session.commit()
        db_session.refresh(concert)
        return concert

    def test_artist_concert_read_from_orm_instance(self, db_session):
        concert = self._build_concert(db_session)

        read = ArtistConcertRead.model_validate(concert)

        assert read.id == concert.id
        assert read.date == concert.date_time

    def test_artist_concert_read_nests_venue_with_city(self, db_session):
        concert = self._build_concert(db_session)

        read = ArtistConcertRead.model_validate(concert)

        assert read.venue.id == concert.venue.id
        assert read.venue.name == "Wembley Stadium"
        assert read.venue.city == "London"

    def test_artist_concert_read_rejects_missing_venue(self, db_session):
        tour = Tour(
            name="World Tour",
            artist="Test Artist",
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date(),
        )
        db_session.add(tour)
        db_session.commit()

        class _ConcertWithoutVenue:
            id = 1
            date_time = datetime(2024, 7, 15, 20, 0)
            venue = None

        with pytest.raises(ValidationError):
            ArtistConcertRead.model_validate(_ConcertWithoutVenue())


class TestNextConcertResponse:
    """Test cases for the `NextConcertResponse` schema."""

    def _valid_payload(self):
        return {
            "concert_id": 1,
            "date": datetime(2024, 7, 15, 20, 0),
            "venue_name": "Madison Square Garden",
            "venue_city": "New York",
            "tickets_remaining": 5000,
        }

    def test_valid_payload_serialises_date_to_iso8601(self):
        response = NextConcertResponse(**self._valid_payload())

        dumped = response.model_dump(mode="json")

        assert dumped["date"] == "2024-07-15T20:00:00"

    def test_rejects_negative_tickets_remaining(self):
        payload = self._valid_payload()
        payload["tickets_remaining"] = -1

        with pytest.raises(ValidationError):
            NextConcertResponse(**payload)

    def test_accepts_zero_tickets_remaining(self):
        payload = self._valid_payload()
        payload["tickets_remaining"] = 0

        response = NextConcertResponse(**payload)

        assert response.tickets_remaining == 0

    def test_rejects_empty_venue_name(self):
        payload = self._valid_payload()
        payload["venue_name"] = ""

        with pytest.raises(ValidationError):
            NextConcertResponse(**payload)

    def test_rejects_empty_venue_city(self):
        payload = self._valid_payload()
        payload["venue_city"] = ""

        with pytest.raises(ValidationError):
            NextConcertResponse(**payload)

    def test_builds_from_attribute_holding_object(self):
        class _NextConcert:
            concert_id = 7
            date = datetime(2024, 8, 1, 19, 30)
            venue_name = "Wembley Stadium"
            venue_city = "London"
            tickets_remaining = 120

        response = NextConcertResponse.model_validate(_NextConcert())

        assert response.concert_id == 7
        assert response.venue_name == "Wembley Stadium"
        assert response.venue_city == "London"
        assert response.tickets_remaining == 120
