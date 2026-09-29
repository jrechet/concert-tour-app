"""SQLAlchemy model for LineupEntry entity."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, event, select
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from ..database import Base


class LineupEntry(Base):
    """A supporting act performing at a concert.

    `set_order` fixes the display order on the concert detail page (lower
    plays earlier); the headliner is excluded here since it's already shown
    separately. It is independent of `set_time`, which is an optional
    scheduled stage time shown alongside the act when known.
    """

    __tablename__ = "lineup_entries"
    __table_args__ = (
        UniqueConstraint("concert_id", "set_order", name="uq_lineup_entries_concert_id_set_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    concert_id = Column(Integer, ForeignKey("concerts.id"), nullable=False, index=True)
    artist_name = Column(String(200), nullable=False)
    set_order = Column(Integer, nullable=False)
    set_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    concert = relationship("Concert", back_populates="lineup")

    @validates("set_order")
    def validate_set_order(self, key, value):
        """Reject a negative running-order position."""
        if value is not None and value < 0:
            raise ValueError("set_order cannot be negative")
        return value


def _reject_duplicate_set_order(connection, target):
    """Reject a `set_order` already used by another entry on the same concert.

    Runs as a mapper-level flush event (rather than a `@validates` hook) so
    it still catches the conflict when the duplicate is only visible once
    both rows are about to be written: a `@validates` hook can't see sibling
    rows if the new entry hasn't been added to a session yet at the point
    `set_order` is assigned, which is the common construction pattern
    (`LineupEntry(concert_id=..., set_order=...)` before `session.add()`).

    This raises a friendlier `ValueError` before the flush even reaches the
    database; the `UniqueConstraint` in `__table_args__` is the backstop that
    still enforces the rule for any write path that bypasses this event.
    """
    table = LineupEntry.__table__
    query = select(table.c.id).where(
        table.c.concert_id == target.concert_id,
        table.c.set_order == target.set_order,
    )
    if target.id is not None:
        query = query.where(table.c.id != target.id)
    if connection.execute(query).first() is not None:
        raise ValueError(
            f"set_order {target.set_order} is already used for concert {target.concert_id}"
        )


@event.listens_for(LineupEntry, "before_insert")
def _check_unique_set_order_before_insert(mapper, connection, target):
    _reject_duplicate_set_order(connection, target)


@event.listens_for(LineupEntry, "before_update")
def _check_unique_set_order_before_update(mapper, connection, target):
    _reject_duplicate_set_order(connection, target)
