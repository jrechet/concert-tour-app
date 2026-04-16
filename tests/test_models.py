"""Tests for Song and Setlist models."""

import pytest
from sqlalchemy.exc import IntegrityError
from models import Song, Setlist, SetlistSong, db


class TestSongModel:
    """Test cases for the Song model."""

    def test_song_creation(self, app):
        """Test creating a song with valid data."""
        song = Song(
            title="Test Song",
            artist="Test Artist",
            duration=180
        )
        db.session.add(song)
        db.session.commit()
        
        assert song.id is not None
        assert song.title == "Test Song"
        assert song.artist == "Test Artist"
        assert song.duration == 180
        assert song.created_at is not None
        assert song.updated_at is not None

    def test_song_string_representation(self, app):
        """Test song string representation."""
        song = Song(title="Test Song", artist="Test Artist", duration=180)
        assert str(song) == "Test Song by Test Artist"

    def test_song_duration_minutes_property(self, app):
        """Test duration_minutes property calculation."""
        song = Song(title="Test", artist="Artist", duration=150)  # 2:30
        assert song.duration_minutes == "2:30"
        
        song.duration = 60  # 1:00
        assert song.duration_minutes == "1:00"
        
        song.duration = 75  # 1:15
        assert song.duration_minutes == "1:15"
        
        song.duration = 0  # 0:00
        assert song.duration_minutes == "0:00"

    def test_song_title_required(self, app):
        """Test that title is required."""
        song = Song(artist="Test Artist", duration=180)
        db.session.add(song)
        
        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_song_artist_required(self, app):
        """Test that artist is required."""
        song = Song(title="Test Song", duration=180)
        db.session.add(song)
        
        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_song_duration_defaults_to_zero(self, app):
        """Test that duration defaults to 0."""
        song = Song(title="Test Song", artist="Test Artist")
        db.session.add(song)
        db.session.commit()
        
        assert song.duration == 0

    def test_song_negative_duration_validation(self, app):
        """Test that negative duration is handled."""
        song = Song(title="Test Song", artist="Test Artist", duration=-10)
        db.session.add(song)
        db.session.commit()
        
        # Model allows negative values, validation should be in forms/API
        assert song.duration == -10


class TestSetlistModel:
    """Test cases for the Setlist model."""

    def test_setlist_creation(self, app):
        """Test creating a setlist with valid data."""
        setlist = Setlist(name="Test Setlist")
        db.session.add(setlist)
        db.session.commit()
        
        assert setlist.id is not None
        assert setlist.name == "Test Setlist"
        assert setlist.created_at is not None
        assert setlist.updated_at is not None

    def test_setlist_string_representation(self, app):
        """Test setlist string representation."""
        setlist = Setlist(name="My Setlist")
        assert str(setlist) == "My Setlist"

    def test_setlist_name_required(self, app):
        """Test that name is required."""
        setlist = Setlist()
        db.session.add(setlist)
        
        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_empty_setlist_total_duration(self, app):
        """Test total duration calculation for empty setlist."""
        setlist = Setlist(name="Empty Setlist")
        db.session.add(setlist)
        db.session.commit()
        
        assert setlist.total_duration == 0
        assert setlist.total_duration_minutes == "0:00"

    def test_setlist_with_songs_total_duration(self, app, sample_songs):
        """Test total duration calculation with songs."""
        setlist = Setlist(name="Test Setlist")
        db.session.add(setlist)
        db.session.flush()
        
        # Add songs with durations: 210, 180, 240
        setlist.add_song(sample_songs[0], order_position=0)
        setlist.add_song(sample_songs[1], order_position=1)
        setlist.add_song(sample_songs[2], order_position=2)
        
        db.session.commit()
        
        expected_total = 210 + 180 + 240  # 630 seconds = 10:30
        assert setlist.total_duration == expected_total
        assert setlist.total_duration_minutes == "10:30"

    def test_setlist_add_song(self, app, sample_songs):
        """Test adding a song to setlist."""
        setlist = Setlist(name="Test Setlist")
        db.session.add(setlist)
        db.session.flush()
        
        setlist.add_song(sample_songs[0], order_position=0)
        db.session.commit()
        
        assert len(setlist.songs) == 1
        assert setlist.songs[0].song_id == sample_songs[0].id
        assert setlist.songs[0].order_position == 0

    def test_setlist_remove_song(self, app, sample_setlist):
        """Test removing a song from setlist."""
        initial_count = len(sample_setlist.songs)
        song_to_remove = sample_setlist.songs[1]
        
        sample_setlist.remove_song(song_to_remove.song_id)
        db.session.commit()
        
        assert len(sample_setlist.songs) == initial_count - 1
        # Verify the specific song was removed
        song_ids = [ss.song_id for ss in sample_setlist.songs]
        assert song_to_remove.song_id not in song_ids

    def test_setlist_reorder_songs(self, app, sample_setlist):
        """Test reordering songs in setlist."""
        # Get initial order
        initial_songs = [(ss.song_id, ss.order_position) for ss in sample_setlist.songs]
        
        # Create new order (reverse the order)
        new_order = [ss.song_id for ss in reversed(sample_setlist.songs)]
        
        sample_setlist.reorder_songs(new_order)
        db.session.commit()
        
        # Verify new order
        reordered_songs = sorted(sample_setlist.songs, key=lambda x: x.order_position)
        for i, song in enumerate(reordered_songs):
            assert song.song_id == new_order[i]
            assert song.order_position == i

    def test_setlist_songs_property_ordering(self, app, sample_setlist):
        """Test that songs property returns ordered songs."""
        songs = sample_setlist.songs
        
        # Verify songs are ordered by order_position
        for i in range(1, len(songs)):
            assert songs[i-1].order_position <= songs[i].order_position

    def test_setlist_clone(self, app, sample_setlist):
        """Test cloning a setlist."""
        clone_name = "Cloned Setlist"
        cloned_setlist = sample_setlist.clone(clone_name)
        
        assert cloned_setlist.id != sample_setlist.id
        assert cloned_setlist.name == clone_name
        assert len(cloned_setlist.songs) == len(sample_setlist.songs)
        
        # Verify songs are the same but setlist_song records are different
        for i, original_song in enumerate(sample_setlist.songs):
            cloned_song = cloned_setlist.songs[i]
            assert cloned_song.song_id == original_song.song_id
            assert cloned_song.order_position == original_song.order_position
            assert cloned_song.id != original_song.id
            assert cloned_song.setlist_id == cloned_setlist.id


class TestSetlistSongModel:
    """Test cases for the SetlistSong association model."""

    def test_setlist_song_creation(self, app, sample_songs):
        """Test creating a setlist-song association."""
        setlist = Setlist(name="Test Setlist")
        db.session.add(setlist)
        db.session.flush()
        
        setlist_song = SetlistSong(
            setlist_id=setlist.id,
            song_id=sample_songs[0].id,
            order_position=0
        )
        db.session.add(setlist_song)
        db.session.commit()
        
        assert setlist_song.id is not None
        assert setlist_song.setlist_id == setlist.id
        assert setlist_song.song_id == sample_songs[0].id
        assert setlist_song.order_position == 0

    def test_setlist_song_relationships(self, app, sample_setlist):
        """Test relationships in SetlistSong model."""
        setlist_song = sample_setlist.songs[0]
        
        assert setlist_song.setlist == sample_setlist
        assert setlist_song.song is not None
        assert setlist_song.song.id == setlist_song.song_id

    def test_setlist_song_unique_constraint(self, app, sample_songs):
        """Test that song can't be added twice to same setlist."""
        setlist = Setlist(name="Test Setlist")
        db.session.add(setlist)
        db.session.flush()
        
        # Add song once
        setlist_song1 = SetlistSong(
            setlist_id=setlist.id,
            song_id=sample_songs[0].id,
            order_position=0
        )
        db.session.add(setlist_song1)
        db.session.commit()
        
        # Try to add same song again
        setlist_song2 = SetlistSong(
            setlist_id=setlist.id,
            song_id=sample_songs[0].id,
            order_position=1
        )
        db.session.add(setlist_song2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_setlist_song_order_position_defaults_to_zero(self, app, sample_songs):
        """Test that order_position defaults to 0."""
        setlist = Setlist(name="Test Setlist")
        db.session.add(setlist)
        db.session.flush()
        
        setlist_song = SetlistSong(
            setlist_id=setlist.id,
            song_id=sample_songs[0].id
        )
        db.session.add(setlist_song)
        db.session.commit()
        
        assert setlist_song.order_position == 0
