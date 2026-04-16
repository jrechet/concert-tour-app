from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum


class Base(DeclarativeBase):
    pass


class TourStatus(enum.Enum):
    planning = "planning"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class ConcertStatus(enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class TicketStatus(enum.Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"
    cancelled = "cancelled"


class Tour(Base):
    __tablename__ = "tours"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(TourStatus), nullable=False, default=TourStatus.planning)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    concerts = relationship("Concert", back_populates="tour")


class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    concerts = relationship("Concert", back_populates="venue")


class Concert(Base):
    __tablename__ = "concerts"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    doors_open = Column(DateTime(timezone=True))
    show_start = Column(DateTime(timezone=True))
    status = Column(Enum(ConcertStatus), nullable=False, default=ConcertStatus.scheduled)
    base_price = Column(Decimal(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    tour = relationship("Tour", back_populates="concerts")
    venue = relationship("Venue", back_populates="concerts")
    tickets = relationship("Ticket", back_populates="concert")


class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    concert_id = Column(Integer, ForeignKey("concerts.id"), nullable=False)
    seat_number = Column(String(50))
    section = Column(String(50))
    price = Column(Decimal(10, 2), nullable=False)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.available)
    customer_name = Column(String(200))
    customer_email = Column(String(200))
    purchased_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    concert = relationship("Concert", back_populates="tickets")
