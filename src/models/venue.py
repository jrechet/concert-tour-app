from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime, func
from datetime import datetime
import re


class Base(DeclarativeBase):
    pass


class Venue(Base):
    __tablename__ = 'venues'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_size: Mapped[str] = mapped_column(String(100), nullable=False)
    sound_system: Mapped[str] = mapped_column(String(255), nullable=False)
    lighting_rig: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __init__(self, **kwargs):
        # Validate capacity is positive
        if 'capacity' in kwargs:
            if kwargs['capacity'] <= 0:
                raise ValueError("Capacity must be a positive integer")
        
        # Validate email format
        if 'contact_email' in kwargs:
            if not self._is_valid_email(kwargs['contact_email']):
                raise ValueError("Invalid email format")
        
        super().__init__(**kwargs)
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format using regex."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def __repr__(self):
        return f"<Venue(id={self.id}, name='{self.name}', city='{self.city}', capacity={self.capacity})>"
