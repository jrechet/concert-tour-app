from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./concert_tour.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
