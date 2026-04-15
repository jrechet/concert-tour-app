from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from src.database import Base


class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    band_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="planned")

    # Relationship to concerts
    concerts = relationship("Concert", back_populates="tour")
