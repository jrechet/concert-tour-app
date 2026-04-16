from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Decimal, Enum
from sqlalchemy.orm import relationship
from src.database import Base
import enum


class TourStatus(enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConcertStatus(enum.Enum):
    SCHEDULED = "scheduled"
    SOLD_OUT = "sold_out"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(TourStatus), nullable=False, default=TourStatus.PLANNING)

    # Relationships
    concerts = relationship("Concert", back_populates="tour", cascade="all, delete-orphan")


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)

    # Relationships
    concerts = relationship("Concert", back_populates="venue")


class Concert(Base):
    __tablename__ = "concerts"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    ticket_price = Column(Decimal(10, 2), nullable=False)
    status = Column(Enum(ConcertStatus), nullable=False, default=ConcertStatus.SCHEDULED)

    # Relationships
    tour = relationship("Tour", back_populates="concerts")
    venue = relationship("Venue", back_populates="concerts")
