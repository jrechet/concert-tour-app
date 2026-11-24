"""SQLAlchemy model for Concert entity."""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, Numeric, String, event
from sqlalchemy.orm import relationship, validates

from ..config import ALMOST_SOLD_OUT_THRESHOLD
from ..database import Base, get_reference_time
from .exceptions import ConcertDateInPastError, ConcertNotCancelledError


class ConcertStatus(str, enum.Enum):
    """Lifecycle status for a `Concert`.

    The single source of truth for valid status values: the model's
    `status` column, the `migrations/versions/*_add_concert_status.py`
    migration, and `src.schemas.concert` all reuse this enum rather than
    duplicating the `scheduled`/`cancelled` string literals.
    """

    scheduled = "scheduled"
    cancelled = "cancelled"


class Concert(Base):
    """Concert database model, linking a Tour to a Venue on a given date."""

    __tablename__ = "concerts"
    __table_args__ = (
        Index("ix_concerts_venue_id_date_time", "venue_id", "date_time"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False, index=True)
    date_time = Column(DateTime, nullable=False, index=True)
    ticket_price = Column(Numeric(10, 2), nullable=True)
    capacity = Column(Integer, nullable=True)
    tickets_sold = Column(Integer, nullable=False, default=0)
    is_cancelled = Column(Boolean, nullable=False, default=False, server_default="0")
    cancellation_reason = Column(String(500), nullable=True)
    cancelled_with_tour = Column(Boolean, nullable=False, default=False, server_default="0")
    notes = Column(String(500), nullable=True, default=None)
    status = Column(
        SAEnum(
            ConcertStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            name="concert_status",
        ),
        nullable=False,
        default=ConcertStatus.scheduled,
        server_default=ConcertStatus.scheduled.value,
    )

    tour = relationship("Tour", backref="concerts")
    venue = relationship("Venue", backref="concerts")
    lineup = relationship(
        "LineupEntry",
        back_populates="concert",
        cascade="all, delete-orphan",
        order_by="LineupEntry.set_order",
    )
    tiers = relationship(
        "TicketTier",
        back_populates="concert",
        cascade="all, delete-orphan",
    )

    @validates("capacity")
    def validate_capacity(self, key, value):
        """Reject a negative capacity. `None` is allowed, meaning this
        concert has no capacity of its own and falls back to its venue's
        capacity (see `_effective_capacity`).
        """
        if value is not None and value < 0:
            raise ValueError("capacity cannot be negative")
        return value

    @validates("tickets_sold")
    def validate_tickets_sold(self, key, value):
        """Reject negative sales counts and sales that exceed this
        concert's effective capacity: its own `capacity` when set,
        otherwise the venue's capacity (when the venue is already attached
        to this concert).
        """
        if value is None:
            return value
        if value < 0:
            raise ValueError("tickets_sold cannot be negative")
        capacity = self.capacity
        if capacity is None and self.venue is not None:
            capacity = self.venue.capacity
        if capacity is not None and value > capacity:
            raise ValueError("tickets_sold cannot exceed capacity")
        return value

    @validates("status")
    def validate_status(self, key, value):
        """Coerce a plain string to `ConcertStatus`, rejecting any value
        that isn't a known member, immediately rather than at flush time.
        """
        if isinstance(value, ConcertStatus):
            return value
        try:
            return ConcertStatus(value)
        except ValueError as exc:
            raise ValueError(f"Invalid concert status: {value!r}") from exc

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
    def _effective_capacity(self):
        """This concert's own `capacity` when set, otherwise its venue's
        capacity, otherwise `None` when neither is known."""
        if self.capacity is not None:
            return self.capacity
        return self.venue.capacity if self.venue is not None else None

    @property
    def tickets_remaining(self):
        """Tickets still available, derived from `_effective_capacity`
        and `tickets_sold`, clamped to never go below 0.

        Returns `None` when no capacity (own or the venue's) is known,
        since remaining count can't be computed without one.
        """
        capacity = self._effective_capacity
        if capacity is None:
            return None
        return max(capacity - (self.tickets_sold or 0), 0)

    @property
    def percentage_sold(self):
        """Tickets sold as a percentage of venue capacity, rounded to 1
        decimal place, mirroring `OccupancyResponse.percentage_sold`.

        Returns None when the venue has no known (or zero) capacity, since
        a percentage can't be meaningfully computed in either case.
        """
        capacity = self.venue.capacity if self.venue is not None else None
        if not capacity:
            return None
        return round((self.tickets_sold or 0) / capacity * 100, 1)

    @property
    def sold_out(self):
        """Whether every ticket for this concert has been sold."""
        remaining = self.remaining_tickets
        return remaining is not None and remaining <= 0

    @property
    def is_sold_out(self):
        """Whether every ticket for this concert has been sold, based on
        `tickets_remaining`. `False` when no capacity (own or the venue's)
        is known, since sold-out status can't be determined without one.
        """
        remaining = self.tickets_remaining
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

    @property
    def days_until_concert(self):
        """Calendar days from `get_reference_time()` until this concert's
        date. Compares dates only (not exact timestamps), so a concert later
        today is 0 days away rather than a fractional day, and the result is
        negative once the concert's date has passed.
        """
        return (self.date_time.date() - get_reference_time().date()).days

    def uncancel(self):
        """Restore a cancelled concert to `ConcertStatus.scheduled`, in place.

        Raises `ConcertNotCancelledError` when `status` isn't
        `ConcertStatus.cancelled` (the message names the current status).
        This check runs first, so a concert that is both not cancelled and
        past-dated always raises `ConcertNotCancelledError`, never
        `ConcertDateInPastError` -- deterministic, so a caller (e.g. the API
        layer) can rely on the raised type to report which rule failed.

        Raises `ConcertDateInPastError` when the concert is cancelled but
        its calendar date (compared via `get_reference_time()`, not the
        real wall clock, so callers can control "now") has already passed.

        On success, only `status` changes, to `ConcertStatus.scheduled`;
        every other field is left untouched.
        """
        if self.status != ConcertStatus.cancelled:
            raise ConcertNotCancelledError(
                f"Concert is not cancelled (status: {self.status.value})"
            )

        if self.date_time.date() < get_reference_time().date():
            raise ConcertDateInPastError(
                f"Concert cannot be uncancelled: date {self.date_time.date()} is in the past"
            )

        self.status = ConcertStatus.scheduled


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
