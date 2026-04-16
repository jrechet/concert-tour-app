from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import EmailStr, validator
import re

Base = declarative_base()


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    address = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=True)
    stage_size = Column(String(100), nullable=True)
    sound_system = Column(String(200), nullable=True)
    lighting_rig = Column(String(200), nullable=True)
    contact_name = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Venue(id={self.id}, name='{self.name}', city='{self.city}', country='{self.country}')>"

    @classmethod
    def validate_email(cls, email):
        """Validate email format"""
        if email is None:
            return True
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    @classmethod
    def validate_capacity(cls, capacity):
        """Validate capacity is positive integer"""
        if capacity is None:
            return True
        return isinstance(capacity, int) and capacity > 0
