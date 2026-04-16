import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from src.models.models import Tour, Concert, Venue, TourStatus, ConcertStatus


class TestTourModel:
    def test_create_tour(self, db_session):
        tour = Tour(
            name="Summer Tour 2024",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=90),
            status=TourStatus.PLANNING
        )
        db_session.add(tour)
        db_session.commit()
        
        assert tour.id is not None
        assert tour.name == "Summer Tour 2024"
        assert tour.status == TourStatus.PLANNING

    def test_tour_concert_relationship(self, db_session, sample_tour, sample_venue):
        # Create a concert for the tour
        concert = Concert(
            tour_id=sample_tour.id,
            venue_id=sample_venue.id,
            date=datetime.now() + timedelta(days=30),
            capacity=15000,
            ticket_price=Decimal("50.00"),
            status=ConcertStatus.SCHEDULED
        )
        db_session.add(concert)
        db_session.commit()
        
        # Test relationship
        assert len(sample_tour.concerts) == 1
        assert sample_tour.concerts[0] == concert
        assert concert.tour == sample_tour

    def test_tour_cascade_delete(self, db_session, sample_tour, sample_venue):
        # Create a concert for the tour
        concert = Concert(
            tour_id=sample_tour.id,
            venue_id=sample_venue.id,
            date=datetime.now() + timedelta(days=30),
            capacity=15000,
            ticket_price=Decimal("50.00"),
            status=ConcertStatus.SCHEDULED
        )
        db_session.add(concert)
        db_session.commit()
        
        # Delete the tour
        db_session.delete(sample_tour)
        db_session.commit()
        
        # Concert should be deleted as well due to cascade
        remaining_concerts = db_session.query(Concert).filter(Concert.tour_id == sample_tour.id).all()
        assert len(remaining_concerts) == 0


class TestVenueModel:
    def test_create_venue(self, db_session):
        venue = Venue(
            name="Red Rocks Amphitheatre",
            city="Morrison",
            country="USA",
            capacity=9525
        )
        db_session.add(venue)
        db_session.commit()
        
        assert venue.id is not None
        assert venue.name == "Red Rocks Amphitheatre"
        assert venue.city == "Morrison"
        assert venue.capacity == 9525

    def test_venue_concert_relationship(self, db_session, sample_venue, sample_tour):
        # Create a concert at the venue
        concert = Concert(
            tour_id=sample_tour.id,
            venue_id=sample_venue.id,
            date=datetime.now() + timedelta(days=30),
            capacity=sample_venue.capacity,
            ticket_price=Decimal("85.00"),
            status=ConcertStatus.SCHEDULED
        )
        db_session.add(concert)
        db_session.commit()
        
        # Test relationship
        assert len(sample_venue.concerts) == 1
        assert sample_venue.concerts[0] == concert
        assert concert.venue == sample_venue


class TestConcertModel:
    def test_create_concert(self, db_session, sample_tour, sample_venue):
        concert = Concert(
            tour_id=sample_tour.id,
            venue_id=sample_venue.id,
            date=datetime.now() + timedelta(days=60),
            capacity=18000,
            ticket_price=Decimal("95.50"),
            status=ConcertStatus.SCHEDULED
        )
        db_session.add(concert)
        db_session.commit()
        
        assert concert.id is not None
        assert concert.tour_id == sample_tour.id
        assert concert.venue_id == sample_venue.id
        assert concert.ticket_price == Decimal("95.50")
        assert concert.status == ConcertStatus.SCHEDULED

    def test_concert_relationships(self, db_session, sample_concert):
        # Test that concert has proper relationships to tour and venue
        assert sample_concert.tour is not None
        assert sample_concert.venue is not None
        assert sample_concert.tour.name == "World Tour 2024"
        assert sample_concert.venue.name == "Madison Square Garden"

    def test_concert_status_enum(self, db_session, sample_tour, sample_venue):
        concert = Concert(
            tour_id=sample_tour.id,
            venue_id=sample_venue.id,
            date=datetime.now() + timedelta(days=60),
            capacity=18000,
            ticket_price=Decimal("95.50"),
            status=ConcertStatus.SOLD_OUT
        )
        db_session.add(concert)
        db_session.commit()
        
        assert concert.status == ConcertStatus.SOLD_OUT

    def test_foreign_key_constraints(self, db_session):
        # Test that foreign key constraints are enforced
        with pytest.raises(Exception):
            concert = Concert(
                tour_id=999,  # Non-existent tour
                venue_id=999,  # Non-existent venue
                date=datetime.now(),
                capacity=1000,
                ticket_price=Decimal("50.00"),
                status=ConcertStatus.SCHEDULED
            )
            db_session.add(concert)
            db_session.commit()
