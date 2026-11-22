"""SQLAlchemy model for Artist entity."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, validates

from ..database import Base

ARTIST_NAME_MAX_LENGTH = 200


class Artist(Base):
    """Artist database model.

    Linked to the concerts it plays through `LineupEntry.artist_id` (the
    existing lineup association table) rather than a second, independent
    FK on `Concert` -- there is exactly one artist-to-concert link.
    `concerts` is `viewonly` because `LineupEntry` carries its own identity
    (`set_order`, `set_time`) that this relationship doesn't manage.
    """

    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(ARTIST_NAME_MAX_LENGTH), nullable=False)

    concerts = relationship(
        "Concert",
        secondary="lineup_entries",
        viewonly=True,
        order_by="Concert.date_time",
    )

    @validates("name")
    def validate_name(self, key, value):
        """Reject an empty or whitespace-only name, mirroring `Venue.validate_name`."""
        if value is None or not value.strip():
            raise ValueError("name must not be empty or whitespace")
        return value
