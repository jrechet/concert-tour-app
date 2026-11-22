"""SQLAlchemy model for Artist entity."""

from sqlalchemy import Column, Integer, String, UniqueConstraint
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

    `name` carries a single named unique constraint (`uq_artists_name`,
    backed by `migrations/versions/2fa2316309a8_add_unique_artist_name.py`)
    so two concurrent renames to the same name can't both succeed, and so
    the 409 handling for that case can key off the constraint name rather
    than parsing a driver-specific error message. It's declared only once,
    here in `__table_args__`, rather than also via `Column(unique=True)`:
    SQLite would otherwise create a second, unnamed unique index alongside
    this one, and an `IntegrityError` could then reference either index
    depending on which one the database happens to check first.
    """

    __tablename__ = "artists"
    __table_args__ = (
        UniqueConstraint("name", name="uq_artists_name"),
    )

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
