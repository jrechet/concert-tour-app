import pytest
from datetime import datetime
from src.models.venue import Venue
from src.models.concert import Concert
from src.models.song import Song
from src.models.setlist import Setlist


def test_model_imports():
    """Test that all models can be imported successfully."""
    from src.models import Venue, Concert, Song, Setlist
    
    # Verify all models are importable and have correct table names
    assert Venue.__tablename__ == "venues"
    assert Concert.__tablename__ == "concerts"
    assert Song.__tablename__ == "songs"
    assert Setlist.__tablename__ == "setlists"


def test_full_setlist_workflow():
    """Test creating a complete setlist with relationships."""
    # Create venue
    venue = Venue(
        name="Madison Square Garden",
        city="New York",
        state="NY"
    )
    
    # Create concert
    concert = Concert(
        venue_id=1,  # Would be venue.id in real scenario
        date=datetime(2024, 6, 15, 20, 0),
        title="Summer Tour 2024"
    )
    
    # Create songs
    song1 = Song(title="Opening Number", duration_minutes=4.5)
    song2 = Song(title="Crowd Favorite", duration_minutes=3.2)
    
    # Create setlist items
    setlist_item1 = Setlist(
        concert_id=1,  # Would be concert.id
        song_id=1,     # Would be song1.id
        order_position=1
    )
    
    setlist_item2 = Setlist(
        concert_id=1,  # Would be concert.id
        song_id=2,     # Would be song2.id
        order_position=2
    )
    
    # Verify all objects are created properly
    assert venue.name == "Madison Square Garden"
    assert concert.title == "Summer Tour 2024"
    assert song1.title == "Opening Number"
    assert song2.title == "Crowd Favorite"
    assert setlist_item1.order_position == 1
    assert setlist_item2.order_position == 2


def test_foreign_key_constraints():
    """Test that foreign key relationships are properly defined."""
    # Check that Setlist has the correct foreign keys
    setlist_columns = Setlist.__table__.columns
    
    # Verify foreign key columns exist
    assert 'concert_id' in setlist_columns
    assert 'song_id' in setlist_columns
    
    # Verify foreign key constraints exist
    foreign_keys = Setlist.__table__.foreign_keys
    fk_tables = {fk.column.table.name for fk in foreign_keys}
    
    assert 'concerts' in fk_tables
    assert 'songs' in fk_tables
