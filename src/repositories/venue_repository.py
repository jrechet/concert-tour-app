from sqlalchemy.orm import Session
from typing import List, Optional
from src.models.models import Venue


class VenueRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_venues(self) -> List[Venue]:
        """Get all venues"""
        return self.db.query(Venue).all()

    def get_venue_by_id(self, venue_id: int) -> Optional[Venue]:
        """Get venue by ID"""
        return self.db.query(Venue).filter(Venue.id == venue_id).first()

    def get_venues_by_city(self, city: str) -> List[Venue]:
        """Get venues by city"""
        return self.db.query(Venue).filter(Venue.city.ilike(f"%{city}%")).all()

    def get_venues_by_country(self, country: str) -> List[Venue]:
        """Get venues by country"""
        return self.db.query(Venue).filter(Venue.country.ilike(f"%{country}%")).all()

    def create_venue(self, venue_data: dict) -> Venue:
        """Create a new venue"""
        venue = Venue(**venue_data)
        self.db.add(venue)
        self.db.commit()
        self.db.refresh(venue)
        return venue

    def update_venue(self, venue_id: int, venue_data: dict) -> Optional[Venue]:
        """Update venue by ID"""
        venue = self.get_venue_by_id(venue_id)
        if not venue:
            return None

        for key, value in venue_data.items():
            setattr(venue, key, value)

        self.db.commit()
        self.db.refresh(venue)
        return venue

    def delete_venue(self, venue_id: int) -> bool:
        """Delete venue by ID"""
        venue = self.get_venue_by_id(venue_id)
        if not venue:
            return False

        self.db.delete(venue)
        self.db.commit()
        return True
