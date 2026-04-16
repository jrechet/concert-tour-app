"""SQLAlchemy model for Tour entity."""

from sqlalchemy import Column, Integer, String, Date, Text

from ..database import Base


class Tour(Base):
    """Tour database model."""

    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    artist = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=True, default="planned")
