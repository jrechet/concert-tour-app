"""SQLAlchemy model for Tour entity."""

from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.orm import validates

from ..database import Base

TOUR_NAME_MAX_LENGTH = 120


class Tour(Base):
    """Tour database model."""

    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(TOUR_NAME_MAX_LENGTH), nullable=False)
    artist = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=True, default="planned")

    @validates("name")
    def validate_name(self, key, value):
        """Reject an empty/whitespace-only or over-long name, mirroring
        `Venue.validate_name`/`Artist.validate_name`."""
        if value is None or not value.strip():
            raise ValueError("name must not be empty or whitespace")
        if len(value) > TOUR_NAME_MAX_LENGTH:
            raise ValueError(f"name must not exceed {TOUR_NAME_MAX_LENGTH} characters")
        return value
