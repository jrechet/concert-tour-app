from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime
from src.models.models import Tour, Concert, TourStatus


class TourRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_tours(self) -> List[Tour]:
        """Get all tours"""
        return self.db.query(Tour).all()

    def get_tour_by_id(self, tour_id: int) -> Optional[Tour]:
        """Get tour by ID"""
        return self.db.query(Tour).filter(Tour.id == tour_id).first()

    def get_active_tours(self) -> List[Tour]:
        """Get all active tours"""
        return self.db.query(Tour).filter(Tour.status == TourStatus.ACTIVE).all()

    def get_tour_overview(self, tour_id: int) -> dict:
        """Get tour overview with statistics"""
        tour = self.get_tour_by_id(tour_id)
        if not tour:
            return None

        # Get concert statistics
        concert_stats = (
            self.db.query(
                func.count(Concert.id).label("total_concerts"),
                func.sum(Concert.capacity).label("total_capacity"),
                func.avg(Concert.ticket_price).label("avg_ticket_price")
            )
            .filter(Concert.tour_id == tour_id)
            .first()
        )

        return {
            "tour": tour,
            "total_concerts": concert_stats.total_concerts or 0,
            "total_capacity": concert_stats.total_capacity or 0,
            "avg_ticket_price": float(concert_stats.avg_ticket_price) if concert_stats.avg_ticket_price else 0
        }

    def create_tour(self, tour_data: dict) -> Tour:
        """Create a new tour"""
        tour = Tour(**tour_data)
        self.db.add(tour)
        self.db.commit()
        self.db.refresh(tour)
        return tour

    def update_tour(self, tour_id: int, tour_data: dict) -> Optional[Tour]:
        """Update tour by ID"""
        tour = self.get_tour_by_id(tour_id)
        if not tour:
            return None

        for key, value in tour_data.items():
            setattr(tour, key, value)

        self.db.commit()
        self.db.refresh(tour)
        return tour

    def delete_tour(self, tour_id: int) -> bool:
        """Delete tour by ID"""
        tour = self.get_tour_by_id(tour_id)
        if not tour:
            return False

        self.db.delete(tour)
        self.db.commit()
        return True
