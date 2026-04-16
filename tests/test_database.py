import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base, create_tables, get_db, SQLALCHEMY_DATABASE_URL


def test_database_creation():
    """Test that database can be created"""
    # Use in-memory SQLite for testing
    test_engine = create_engine("sqlite:///:memory:")
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Test connection
    with TestSessionLocal() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_get_db():
    """Test database dependency function"""
    db_generator = get_db()
    db = next(db_generator)
    assert db is not None
    
    # Clean up
    try:
        next(db_generator)
    except StopIteration:
        pass  # Expected behavior


def test_create_tables():
    """Test that create_tables function works"""
    # This will create tables in the test database
    try:
        create_tables()
    except Exception as e:
        pytest.fail(f"create_tables() raised an exception: {e}")
