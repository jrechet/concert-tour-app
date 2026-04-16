from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import String, Integer, DateTime, Date, Time, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TourStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"


class Tour(Base):
    __tablename__ = "tours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    band_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TourStatus] = mapped_column(String(20), nullable=False, default=TourStatus.PLANNING)

    # Relationship to concerts
    concerts: Mapped[List["Concert"]] = relationship("Concert", back_populates="tour", cascade="all, delete-orphan")

    # Add constraint to ensure end_date is after start_date
    __table_args__ = (
        CheckConstraint('end_date >= start_date', name='check_tour_date_order'),
    )

    def __repr__(self) -> str:
        return f"<Tour(id={self.id}, name='{self.name}', band='{self.band_name}', status='{self.status}')>"


class Concert(Base):
    __tablename__ = "concerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tour_id: Mapped[int] = mapped_column(Integer, ForeignKey("tours.id"), nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    ticket_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationship to tour
    tour: Mapped["Tour"] = relationship("Tour", back_populates="concerts")

    # Add constraints for capacity and ticket_price
    __table_args__ = (
        CheckConstraint('capacity >= 0', name='check_non_negative_capacity'),
        CheckConstraint('ticket_price > 0', name='check_positive_ticket_price'),
    )

    def __repr__(self) -> str:
        return f"<Concert(id={self.id}, venue='{self.venue}', city='{self.city}', date={self.date})>"
