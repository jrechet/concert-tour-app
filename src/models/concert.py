"""SQLAlchemy model for Concert entity."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from ..database import Base


class Concert(Base):
    """Concert database model, linking a Tour to a Venue on a given date."""

    __tablename__ = "concerts"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False, index=True)
    date_time = Column(DateTime, nullable=False)
    ticket_price = Column(Numeric(10, 2), nullable=True)

    tour = relationship("Tour", backref="concerts")
    venue = relationship("Venue", backref="concerts")
