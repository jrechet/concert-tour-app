"""SQLAlchemy model for Venue entity."""

from sqlalchemy import Column, Integer, String

from ..database import Base


class Venue(Base):
    """Venue database model."""

    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=True)
