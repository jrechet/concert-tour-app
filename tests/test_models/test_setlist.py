import pytest
from datetime import datetime
from src.models.setlist import Setlist


def test_setlist_creation():
    """Test creating a Setlist instance."""
    setlist = Setlist(
        concert_id=1,
        song_id=2,
        order_position=3
    )
    
    assert setlist.concert_id == 1
    assert setlist.song_id == 2
    assert setlist.order_position == 3


def test_setlist_repr():
    """Test Setlist string representation."""
    setlist = Setlist(
        id=1,
        concert_id=2,
        song_id=3,
        order_position=4
    )
    expected = "<Setlist(id=1, concert_id=2, song_id=3, order_position=4)>"
    assert repr(setlist) == expected


def test_setlist_required_fields():
    """Test that all required fields are present."""
    setlist = Setlist(
        concert_id=1,
        song_id=2,
        order_position=1
    )
    
    # All fields should be set
    assert setlist.concert_id is not None
    assert setlist.song_id is not None
    assert setlist.order_position is not None
    assert hasattr(setlist, 'created_at')


def test_setlist_relationships():
    """Test that relationship attributes exist."""
    setlist = Setlist(
        concert_id=1,
        song_id=2,
        order_position=1
    )
    
    # Relationship attributes should exist (even if not loaded)
    assert hasattr(setlist, 'concert')
    assert hasattr(setlist, 'song')
