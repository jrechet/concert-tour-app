from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from src.database import Base


class Concert(Base):
    __tablename__ = "concerts"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    venue = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    capacity = Column(Integer, nullable=False)
    ticket_price = Column(Numeric(10, 2), nullable=False)

    # Relationship to tour
    tour = relationship("Tour", back_populates="concerts")
