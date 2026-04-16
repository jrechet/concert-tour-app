from sqlalchemy import Column, Integer, String, Date, Time, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Tour(Base):
    __tablename__ = "tours"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)
    description = Column(Text)
    
    # Relationship to concerts
    concerts = relationship("Concert", back_populates="tour")


class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    address = Column(String)
    
    # Relationship to concerts
    concerts = relationship("Concert", back_populates="venue")


class Concert(Base):
    __tablename__ = "concerts"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time)
    
    # Relationships
    tour = relationship("Tour", back_populates="concerts")
    venue = relationship("Venue", back_populates="concerts")
