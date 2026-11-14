"""
Unit tests for the ConcertPriceUpdate and ArtistConcertRead Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models import Concert, Tour, Venue
from src.schemas.concert import ArtistConcertRead, ConcertPriceUpdate


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
