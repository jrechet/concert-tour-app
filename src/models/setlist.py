from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.database import Base


class Setlist(Base):
    __tablename__ = "setlists"

    id = Column(Integer, primary_key=True, index=True)
    concert_id = Column(Integer, ForeignKey("concerts.id"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    order_position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    concert = relationship("Concert", back_populates="setlist_items")
    song = relationship("Song")

    def __repr__(self):
        return f"<Setlist(id={self.id}, concert_id={self.concert_id}, song_id={self.song_id}, order_position={self.order_position})>"
