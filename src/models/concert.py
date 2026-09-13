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
    tickets_sold = Column(Integer, nullable=False, default=0)

    tour = relationship("Tour", backref="concerts")
    venue = relationship("Venue", backref="concerts")

    @property
    def remaining_tickets(self):
        """Tickets still available, derived from the venue's capacity.

        Returns None when the venue has no known capacity, since remaining
        count can't be computed without it.
        """
        if self.venue is None or self.venue.capacity is None:
            return None
        return max(self.venue.capacity - (self.tickets_sold or 0), 0)

    @property
    def sold_out(self):
        """Whether every ticket for this concert has been sold."""
        remaining = self.remaining_tickets
        return remaining is not None and remaining <= 0
