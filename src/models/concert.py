"""SQLAlchemy model for Concert entity."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship, validates

from ..config import ALMOST_SOLD_OUT_THRESHOLD
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

    @validates("tickets_sold")
    def validate_tickets_sold(self, key, value):
        """Reject negative sales counts and sales that exceed the venue's
        capacity (when the venue is already attached to this concert).
        """
        if value is None:
            return value
        if value < 0:
            raise ValueError("tickets_sold cannot be negative")
        if self.venue is not None and self.venue.capacity is not None and value > self.venue.capacity:
            raise ValueError("tickets_sold cannot exceed venue capacity")
        return value

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

    @property
    def is_almost_sold_out(self):
        """Whether fewer than `ALMOST_SOLD_OUT_THRESHOLD` of total tickets remain.

        Returns False when the venue's total capacity is unknown or zero,
        since the remaining-ticket ratio can't be meaningfully computed in
        either case (and a zero capacity would otherwise divide by zero).
        """
        capacity = self.venue.capacity if self.venue is not None else None
        if not capacity:
            return False
        remaining = self.remaining_tickets
        if remaining is None:
            return False
        return (remaining / capacity) < ALMOST_SOLD_OUT_THRESHOLD
