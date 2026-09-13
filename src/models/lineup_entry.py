"""SQLAlchemy model for LineupEntry entity."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from ..database import Base


class LineupEntry(Base):
    """A supporting act performing at a concert.

    `running_order` fixes the display order on the concert detail page
    (lower plays earlier); it is independent of `set_time`, which is an
    optional scheduled time shown alongside the act when known.
    """

    __tablename__ = "lineup_entries"

    id = Column(Integer, primary_key=True, index=True)
    concert_id = Column(Integer, ForeignKey("concerts.id"), nullable=False, index=True)
    artist_name = Column(String(200), nullable=False)
    running_order = Column(Integer, nullable=False)
    set_time = Column(DateTime, nullable=True)

    concert = relationship(
        "Concert",
        backref=backref(
            "lineup", order_by="LineupEntry.running_order", cascade="all, delete-orphan"
        ),
    )
