"""Database configuration and session management."""

import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Overridable so the Alembic migration environment (migrations/env.py) and
# any non-default deployment can point at a different database without a
# code change.
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///concert_tour.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_reference_time() -> datetime:
    """Dependency supplying the "now" used to split upcoming vs. past dates.

    Overridable via `app.dependency_overrides` in tests, so date-based
    ordering assertions don't depend on the real wall clock.
    """
    return datetime.now()
