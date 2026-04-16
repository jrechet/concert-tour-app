from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from src.database import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    duration_minutes = Column(Float, nullable=True)
    key = Column(String(10), nullable=True)
    tempo_bpm = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Song(id={self.id}, title='{self.title}')>"
