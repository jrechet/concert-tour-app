"""Tests for song CRUD API endpoints."""

import json
import pytest
from models import Song, db


class TestSongAPI:
    """Test cases for song API endpoints."""

    def test_get_songs_empty(self, client):
        """Test getting songs when none exist."""
        response = client.get('/api/songs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data == []

    def test_get_songs_with_data(self, client, sample_songs):
        """Test getting songs when data exists."""
        response = client.get('/api/songs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == len(sample_songs)
        
        # Verify structure of first song
        song = data[0]
        assert 'id' in song
        assert 'title' in song
        assert 'artist' in song
        assert 'duration' in song
        assert 'duration_minutes' in song

    def test_create_song_success(self, client):
        """Test creating a song successfully."""
        song_data = {
            'title': 'New Song',
            'artist': 'New Artist',
            'duration': 200
        }
        
        response = client.post('/api/songs', json=song_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['title'] == song_data['title']
        assert data['artist'] == song_data['artist']
        assert data['duration'] == song_data['duration']
        assert 'id' in data
        
        # Verify song was actually created in database
        song = Song.query.get(data['id'])
        assert song is not None
        assert song.title == song_data['title']

    def test_create_song_missing_title(self, client):
        """Test creating a song without title."""
        song_data = {
            'artist': 'New Artist',
            'duration': 200
        }
        
        response = client.post('/api/songs', json=song_data)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'title' in data['error'].lower()

    def test_create_song_missing_artist(self, client):
        """Test creating a song without artist."""
        song_data = {
            'title': 'New Song',
            'duration': 200
        }
        
        response = client.post('/api/songs', json=song_data)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'artist' in data['error'].lower()

    def test_create_song_invalid_duration(self, client):
        """Test creating a song with invalid duration."""
        song_data = {
            'title': 'New Song',
            'artist': 'New Artist',
            'duration': 'invalid'
        }
        
        response = client.post('/api/songs', json=song_data)
        assert response.status_code == 400

    def test_create_song_negative_duration(self, client):
        """Test creating a song with negative duration."""
        song_data = {
            'title': 'New Song',
            'artist': 'New Artist',
            'duration': -10
        }
        
        response = client.post('/api/songs', json=song_data)
        assert response.status_code == 400

    def test_create_song_default_duration(self, client):
        """Test creating a song without duration (should default to 0)."""
        song_data = {
            'title': 'New Song',
            'artist': 'New Artist'
        }
        
        response = client.post('/api/songs', json=song_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['duration'] == 0

    def test_get_song_success(self, client, sample_songs):
        """Test getting a specific song."""
        song = sample_songs[0]
        
        response = client.get(f'/api/songs/{song.id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == song.id
        assert data['title'] == song.title
        assert data['artist'] == song.artist
        assert data['duration'] == song.duration

    def test_get_song_not_found(self, client):
        """Test getting a non-existent song."""
        response = client.get('/api/songs/999')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_update_song_success(self, client, sample_songs):
        """Test updating a song successfully."""
        song = sample_songs[0]
        
        update_data = {
            'title': 'Updated Title',
            'artist': 'Updated Artist',
            'duration': 250
        }
        
        response = client.put(f'/api/songs/{song.id}', json=update_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['title'] == update_data['title']
        assert data['artist'] == update_data['artist']
        assert data['duration'] == update_data['duration']
        
        # Verify changes were saved to database
        updated_song = Song.query.get(song.id)
        assert updated_song.title == update_data['title']
        assert updated_song.artist == update_data['artist']
        assert updated_song.duration == update_data['duration']

    def test_update_song_partial(self, client, sample_songs):
        """Test partial update of a song."""
        song = sample_songs[0]
        original_artist = song.artist
        original_duration = song.duration
        
        update_data = {
            'title': 'New Title Only'
        }
        
        response = client.put(f'/api/songs/{song.id}', json=update_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['title'] == update_data['title']
        assert data['artist'] == original_artist  # Should remain unchanged
        assert data['duration'] == original_duration  # Should remain unchanged

    def test_update_song_not_found(self, client):
        """Test updating a non-existent song."""
        update_data = {
            'title': 'New Title',
            'artist': 'New Artist'
        }
        
        response = client.put('/api/songs/999', json=update_data)
        assert response.status_code == 404

    def test_update_song_invalid_data(self, client, sample_songs):
        """Test updating a song with invalid data."""
        song = sample_songs[0]
        
        update_data = {
            'title': '',  # Empty title should be invalid
            'duration': -10  # Negative duration should be invalid
        }
        
        response = client.put(f'/api/songs/{song.id}', json=update_data)
        assert response.status_code == 400

    def test_delete_song_success(self, client, sample_songs):
        """Test deleting a song successfully."""
        song = sample_songs[0]
        song_id = song.id
        
        response = client.delete(f'/api/songs/{song_id}')
        assert response.status_code == 204
        
        # Verify song was deleted from database
        deleted_song = Song.query.get(song_id)
        assert deleted_song is None

    def test_delete_song_not_found(self, client):
        """Test deleting a non-existent song."""
        response = client.delete('/api/songs/999')
        assert response.status_code == 404

    def test_delete_song_in_setlist(self, client, sample_setlist):
        """Test deleting a song that's in a setlist."""
        # Get a song that's in the setlist
        setlist_song = sample_setlist.songs[0]
        song_id = setlist_song.song_id
        
        response = client.delete(f'/api/songs/{song_id}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'setlist' in data['error'].lower()

    def test_song_search(self, client, sample_songs):
        """Test searching songs by title or artist."""
        # Test searching by title
        response = client.get('/api/songs?search=Song One')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['title'] == 'Song One'
        
        # Test searching by artist
        response = client.get('/api/songs?search=Artist A')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should find songs by Artist A
        artist_a_songs = [s for s in data if s['artist'] == 'Artist A']
        assert len(artist_a_songs) >= 1

    def test_song_pagination(self, client, app):
        """Test song pagination."""
        # Create many songs
        songs = []
        for i in range(25):
            song = Song(
                title=f'Song {i}',
                artist=f'Artist {i}',
                duration=180
            )
            songs.append(song)
            db.session.add(song)
        db.session.commit()
        
        # Test first page
        response = client.get('/api/songs?page=1&per_page=10')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 10
        
        # Test second page
        response = client.get('/api/songs?page=2&per_page=10')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 10

    def test_invalid_json_request(self, client):
        """Test API with invalid JSON."""
        response = client.post(
            '/api/songs',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_missing_content_type(self, client):
        """Test API without proper content type."""
        response = client.post(
            '/api/songs',
            data='{"title": "Test"}',
            content_type='text/plain'
        )
        assert response.status_code == 400
