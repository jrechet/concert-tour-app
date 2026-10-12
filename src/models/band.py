"""SQLAlchemy model for Band entity."""

from sqlalchemy import Column, Integer, String

from ..database import Base


class Band(Base):
    """Band database model.

    Currently populated only by `src.demo.seeder.seed_demo`: no router or
    service creates a `Band` row yet, and `Tour.artist` still independently
    carries the display name shown elsewhere in the app.
    """

    __tablename__ = "bands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
