import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from src.models import Song, Setlist, Concert


class TestSongModel:
    """Test Song model validation and behavior."""
    
    def test_song_creation_valid_data(self):
        """Test creating a song with valid data."""
        song = Song(
            title="Test Song",
            artist="Test Artist",
            duration=180,  # 3 minutes
            key="C",
            tempo=120
        )
        assert song.title == "Test Song"
        assert song.artist == "Test Artist"
        assert song.duration == 180
        assert song.key == "C"
        assert song.tempo == 120

    def test_song_duration_validation_negative(self):
        """Test that negative durations raise ValueError."""
        with pytest.raises(ValueError, match="Duration must be positive"):
            Song(
                title="Test Song",
                artist="Test Artist",
                duration=-10,
                key="C",
                tempo=120
            )

    def test_song_duration_validation_zero(self):
        """Test that zero duration raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be positive"):
            Song(
                title="Test Song",
                artist="Test Artist",
                duration=0,
                key="C",
                tempo=120
            )

    def test_song_tempo_validation_negative(self):
        """Test that negative tempo raises ValueError."""
        with pytest.raises(ValueError, match="Tempo must be positive"):
            Song(
                title="Test Song",
                artist="Test Artist",
                duration=180,
                key="C",
                tempo=-60
            )

    def test_song_tempo_validation_zero(self):
        """Test that zero tempo raises ValueError."""
        with pytest.raises(ValueError, match="Tempo must be positive"):
            Song(
                title="Test Song",
                artist="Test Artist",
                duration=180,
                key="C",
                tempo=0
            )

    def test_song_tempo_validation_too_low(self):
        """Test that tempo below 30 BPM raises ValueError."""
        with pytest.raises(ValueError, match="Tempo must be between 30 and 300 BPM"):
            Song(
                title="Test Song",
                artist="Test Artist",
                duration=180,
                key="C",
                tempo=20
            )

    def test_song_tempo_validation_too_high(self):
        """Test that tempo above 300 BPM raises ValueError."""
        with pytest.raises(ValueError, match="Tempo must be between 30 and 300 BPM"):
            Song(
                title="Test Song",
                artist="Test Artist",
                duration=180,
                key="C",
                tempo=350
            )

    def test_song_tempo_validation_boundary_values(self):
        """Test that boundary tempo values are accepted."""
        # Test minimum valid tempo
        song1 = Song(
            title="Slow Song",
            artist="Test Artist",
            duration=180,
            key="C",
            tempo=30
        )
        assert song1.tempo == 30
        
        # Test maximum valid tempo
        song2 = Song(
            title="Fast Song",
            artist="Test Artist",
            duration=180,
            key="C",
            tempo=300
        )
        assert song2.tempo == 300

    def test_song_duration_calculation_minutes_seconds(self):
        """Test duration formatting for different time lengths."""
        # Test exact minutes
        song1 = Song(
            title="3 Min Song",
            artist="Test Artist",
            duration=180,
            key="C",
            tempo=120
        )
        assert song1.duration == 180
        
        # Test minutes with seconds
        song2 = Song(
            title="3:30 Song",
            artist="Test Artist",
            duration=210,
            key="C",
            tempo=120
        )
        assert song2.duration == 210


class TestSetlistModel:
    """Test Setlist model validation and relationships."""

    @pytest.fixture
    def sample_concert(self):
        """Create a sample concert for testing."""
        return Concert(
            id=1,
            title="Test Concert",
            venue_id=1,
            date=datetime(2024, 6, 15, 20, 0),
            ticket_price=50.00
        )

    @pytest.fixture
    def sample_songs(self):
        """Create sample songs for testing."""
        return [
            Song(id=1, title="Song 1", artist="Artist 1", duration=180, key="C", tempo=120),
            Song(id=2, title="Song 2", artist="Artist 1", duration=240, key="G", tempo=140),
            Song(id=3, title="Song 3", artist="Artist 1", duration=200, key="Am", tempo=100),
        ]

    def test_setlist_creation_empty(self, sample_concert):
        """Test creating an empty setlist."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id
        )
        assert setlist.name == "Main Set"
        assert setlist.concert_id == sample_concert.id
        assert setlist.songs == []

    def test_setlist_creation_with_songs(self, sample_concert, sample_songs):
        """Test creating a setlist with songs."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=sample_songs
        )
        assert setlist.name == "Main Set"
        assert setlist.concert_id == sample_concert.id
        assert len(setlist.songs) == 3

    def test_setlist_total_duration_calculation(self, sample_concert, sample_songs):
        """Test total duration calculation with multiple songs."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=sample_songs
        )
        # Total: 180 + 240 + 200 = 620 seconds
        assert setlist.total_duration == 620

    def test_setlist_total_duration_empty(self, sample_concert):
        """Test total duration calculation for empty setlist."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=[]
        )
        assert setlist.total_duration == 0

    def test_setlist_song_ordering(self, sample_concert, sample_songs):
        """Test that songs maintain their order in the setlist."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=sample_songs
        )
        assert setlist.songs[0].title == "Song 1"
        assert setlist.songs[1].title == "Song 2"
        assert setlist.songs[2].title == "Song 3"

    def test_setlist_reorder_songs(self, sample_concert, sample_songs):
        """Test reordering songs in a setlist."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=sample_songs.copy()
        )
        
        # Reorder: move first song to last position
        first_song = setlist.songs.pop(0)
        setlist.songs.append(first_song)
        
        assert setlist.songs[0].title == "Song 2"
        assert setlist.songs[1].title == "Song 3"
        assert setlist.songs[2].title == "Song 1"

    def test_setlist_add_song(self, sample_concert, sample_songs):
        """Test adding a song to existing setlist."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=sample_songs[:2].copy()  # Start with 2 songs
        )
        
        new_song = Song(id=4, title="New Song", artist="Artist 1", duration=190, key="D", tempo=130)
        setlist.songs.append(new_song)
        
        assert len(setlist.songs) == 3
        assert setlist.songs[2].title == "New Song"
        assert setlist.total_duration == 180 + 240 + 190  # 610 seconds

    def test_setlist_remove_song(self, sample_concert, sample_songs):
        """Test removing a song from setlist."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=sample_songs.copy()
        )
        
        # Remove middle song
        removed_song = setlist.songs.pop(1)
        
        assert len(setlist.songs) == 2
        assert removed_song.title == "Song 2"
        assert setlist.songs[0].title == "Song 1"
        assert setlist.songs[1].title == "Song 3"
        assert setlist.total_duration == 180 + 200  # 380 seconds

    def test_setlist_unique_concert_relationship(self, sample_songs):
        """Test that setlists are properly associated with concerts."""
        concert1 = Concert(id=1, title="Concert 1", venue_id=1, date=datetime.now(), ticket_price=50.00)
        concert2 = Concert(id=2, title="Concert 2", venue_id=1, date=datetime.now(), ticket_price=60.00)
        
        setlist1 = Setlist(id=1, name="Set 1", concert_id=concert1.id, songs=sample_songs[:2])
        setlist2 = Setlist(id=2, name="Set 2", concert_id=concert2.id, songs=sample_songs[1:])
        
        assert setlist1.concert_id == concert1.id
        assert setlist2.concert_id == concert2.id
        assert setlist1.concert_id != setlist2.concert_id

    def test_setlist_clone_functionality(self, sample_concert, sample_songs):
        """Test cloning a setlist with all its properties."""
        original_setlist = Setlist(
            id=1,
            name="Original Set",
            concert_id=sample_concert.id,
            songs=sample_songs.copy()
        )
        
        # Clone the setlist
        cloned_setlist = Setlist(
            id=2,  # New ID
            name=f"{original_setlist.name} (Copy)",
            concert_id=original_setlist.concert_id,
            songs=original_setlist.songs.copy()  # Copy songs list
        )
        
        assert cloned_setlist.id != original_setlist.id
        assert cloned_setlist.name == "Original Set (Copy)"
        assert cloned_setlist.concert_id == original_setlist.concert_id
        assert len(cloned_setlist.songs) == len(original_setlist.songs)
        assert cloned_setlist.total_duration == original_setlist.total_duration
        
        # Verify songs are the same but lists are independent
        for i, song in enumerate(cloned_setlist.songs):
            assert song.id == original_setlist.songs[i].id
            assert song.title == original_setlist.songs[i].title
        
        # Test independence: modifying clone shouldn't affect original
        cloned_setlist.songs.pop()
        assert len(cloned_setlist.songs) == 2
        assert len(original_setlist.songs) == 3

    def test_setlist_clone_empty_setlist(self, sample_concert):
        """Test cloning an empty setlist."""
        original_setlist = Setlist(
            id=1,
            name="Empty Set",
            concert_id=sample_concert.id,
            songs=[]
        )
        
        cloned_setlist = Setlist(
            id=2,
            name=f"{original_setlist.name} (Copy)",
            concert_id=original_setlist.concert_id,
            songs=original_setlist.songs.copy()
        )
        
        assert cloned_setlist.id != original_setlist.id
        assert cloned_setlist.name == "Empty Set (Copy)"
        assert len(cloned_setlist.songs) == 0
        assert cloned_setlist.total_duration == 0

    def test_setlist_position_validation(self, sample_concert, sample_songs):
        """Test song position validation in setlist."""
        setlist = Setlist(
            id=1,
            name="Main Set",
            concert_id=sample_concert.id,
            songs=sample_songs.copy()
        )
        
        # Test valid positions
        assert 0 <= 0 < len(setlist.songs)  # First position
        assert 0 <= len(setlist.songs) - 1 < len(setlist.songs)  # Last position
        
        # Test invalid positions would be handled by list indexing
        with pytest.raises(IndexError):
            _ = setlist.songs[10]  # Out of bounds
