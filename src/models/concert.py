"""SQLAlchemy model for Concert entity."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, event
from sqlalchemy.orm import relationship, validates

from ..config import ALMOST_SOLD_OUT_THRESHOLD
from ..database import Base, get_reference_time


class Concert(Base):
    """Concert database model, linking a Tour to a Venue on a given date."""

    __tablename__ = "concerts"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False, index=True)
    date_time = Column(DateTime, nullable=False, index=True)
    ticket_price = Column(Numeric(10, 2), nullable=True)
    tickets_sold = Column(Integer, nullable=False, default=0)
    is_cancelled = Column(Boolean, nullable=False, default=False, server_default="0")
    cancellation_reason = Column(String(500), nullable=True)

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
    def venue_name(self):
        """The hosting venue's name, or None when no venue is attached."""
        return self.venue.name if self.venue is not None else None

    @property
    def venue_city(self):
        """The hosting venue's city, or None when no venue is attached."""
        return self.venue.city if self.venue is not None else None

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
    def is_sold_out(self):
        """Alias for `sold_out` matching the `is_`-prefixed naming used by
        `is_cancelled`/`is_almost_sold_out`, for API consumers."""
        return self.sold_out

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

    @property
    def days_until_concert(self):
        """Calendar days from `get_reference_time()` until this concert's
        date. Compares dates only (not exact timestamps), so a concert later
        today is 0 days away rather than a fractional day, and the result is
        negative once the concert's date has passed.
        """
        return (self.date_time.date() - get_reference_time().date()).days


@event.listens_for(Concert, "before_insert")
@event.listens_for(Concert, "before_update")
def _enforce_cancellation_consistency(mapper, connection, target):
    """Keep `is_cancelled`/`cancellation_reason` consistent on every flush.

    Checked at flush time (rather than via `@validates` on the individual
    columns) so the rule holds no matter which of the two attributes was
    set first, or whether `cancellation_reason` was ever touched at all.
    """
    if target.is_cancelled:
        if not target.cancellation_reason or not target.cancellation_reason.strip():
            raise ValueError("cancellation_reason must be a non-empty string when is_cancelled is True")
    else:
        target.cancellation_reason = None
