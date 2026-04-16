from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
from src.models.models import Concert, ConcertStatus


class ConcertRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_concerts(self) -> List[Concert]:
        """Get all concerts with venue and tour data"""
        return (
            self.db.query(Concert)
            .options(joinedload(Concert.venue), joinedload(Concert.tour))
            .all()
        )

    def get_concert_by_id(self, concert_id: int) -> Optional[Concert]:
        """Get concert by ID with venue and tour data"""
        return (
            self.db.query(Concert)
            .options(joinedload(Concert.venue), joinedload(Concert.tour))
            .filter(Concert.id == concert_id)
            .first()
        )

    def get_concerts_by_tour(self, tour_id: int) -> List[Concert]:
        """Get all concerts for a specific tour"""
        return (
            self.db.query(Concert)
            .options(joinedload(Concert.venue))
            .filter(Concert.tour_id == tour_id)
            .order_by(Concert.date)
            .all()
        )

    def get_upcoming_concerts(self, limit: Optional[int] = None) -> List[Concert]:
        """Get upcoming concerts ordered by date"""
        query = (
            self.db.query(Concert)
            .options(joinedload(Concert.venue), joinedload(Concert.tour))
            .filter(
                and_(
                    Concert.date >= datetime.now(),
                    Concert.status == ConcertStatus.SCHEDULED
                )
            )
            .order_by(Concert.date)
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_concerts_by_venue(self, venue_id: int) -> List[Concert]:
        """Get all concerts for a specific venue"""
        return (
            self.db.query(Concert)
            .options(joinedload(Concert.tour))
            .filter(Concert.venue_id == venue_id)
            .order_by(Concert.date)
            .all()
        )

    def create_concert(self, concert_data: dict) -> Concert:
        """Create a new concert"""
        concert = Concert(**concert_data)
        self.db.add(concert)
        self.db.commit()
        self.db.refresh(concert)
        return concert

    def update_concert(self, concert_id: int, concert_data: dict) -> Optional[Concert]:
        """Update concert by ID"""
        concert = self.get_concert_by_id(concert_id)
        if not concert:
            return None

        for key, value in concert_data.items():
            setattr(concert, key, value)

        self.db.commit()
        self.db.refresh(concert)
        return concert

    def delete_concert(self, concert_id: int) -> bool:
        """Delete concert by ID"""
        concert = self.get_concert_by_id(concert_id)
        if not concert:
            return False

        self.db.delete(concert)
        self.db.commit()
        return True
