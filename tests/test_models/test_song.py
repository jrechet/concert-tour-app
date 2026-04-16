import pytest
from datetime import datetime
from src.models.song import Song


def test_song_creation():
    """Test creating a Song instance."""
    song = Song(
        title="Bohemian Rhapsody",
        duration_minutes=5.9,
        key="B♭",
        tempo_bpm=72,
        notes="Classic Queen ballad with opera section"
    )
    
    assert song.title == "Bohemian Rhapsody"
    assert song.duration_minutes == 5.9
    assert song.key == "B♭"
    assert song.tempo_bpm == 72
    assert song.notes == "Classic Queen ballad with opera section"


def test_song_repr():
    """Test Song string representation."""
    song = Song(id=1, title="Test Song")
    assert repr(song) == "<Song(id=1, title='Test Song')>"


def test_song_optional_fields():
    """Test Song with only required fields."""
    song = Song(title="Simple Song")
    
    assert song.title == "Simple Song"
    assert song.duration_minutes is None
    assert song.key is None
    assert song.tempo_bpm is None
    assert song.notes is None


def test_song_timestamps():
    """Test that timestamps are set properly."""
    song = Song(title="Test Song")
    
    # created_at and updated_at should be None until saved to database
    # They get set by SQLAlchemy's default when inserting
    assert hasattr(song, 'created_at')
    assert hasattr(song, 'updated_at')
