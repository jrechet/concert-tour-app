import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.main import app
from src.database import get_db, Base
from src.models import Song, Venue, Concert, Setlist

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_setlists.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def sample_data():
    # Create venue
    venue_data = {"name": "Test Venue", "city": "Test City", "state": "TS", "capacity": 1000}
    venue_response = client.post("/api/v1/venues", json=venue_data)
    venue_id = venue_response.json()["id"]
    
    # Create concert
    concert_data = {
        "date": "2024-12-25T19:00:00",
        "venue_id": venue_id,
        "ticket_price": 50.0
    }
    concert_response = client.post("/api/v1/concerts", json=concert_data)
    concert_id = concert_response.json()["id"]
    
    # Create songs
    song1_data = {"title": "Song 1", "artist": "Artist 1", "duration_minutes": 3.0}
    song2_data = {"title": "Song 2", "artist": "Artist 2", "duration_minutes": 4.0}
    
    song1_response = client.post("/api/v1/songs", json=song1_data)
    song2_response = client.post("/api/v1/songs", json=song2_data)
    
    return {
        "venue_id": venue_id,
        "concert_id": concert_id,
        "song1_id": song1_response.json()["id"],
        "song2_id": song2_response.json()["id"]
    }


def test_get_empty_setlist(sample_data):
    response = client.get(f"/api/v1/concerts/{sample_data['concert_id']}/setlist")
    assert response.status_code == 200
    data = response.json()
    assert data["concert_id"] == sample_data["concert_id"]
    assert data["songs"] == []
    assert data["total_duration_minutes"] == 0


def test_add_song_to_setlist(sample_data):
    response = client.post(
        f"/api/v1/concerts/{sample_data['concert_id']}/setlist/songs",
        params={"song_id": sample_data['song1_id']}
    )
    assert response.status_code == 200
    
    # Verify setlist
    setlist_response = client.get(f"/api/v1/concerts/{sample_data['concert_id']}/setlist")
    data = setlist_response.json()
    assert len(data["songs"]) == 1
    assert data["songs"][0]["title"] == "Song 1"
    assert data["total_duration_minutes"] == 3.0


def test_add_multiple_songs_to_setlist(sample_data):
    # Add first song
    client.post(
        f"/api/v1/concerts/{sample_data['concert_id']}/setlist/songs",
        params={"song_id": sample_data['song1_id']}
    )
    
    # Add second song
    client.post(
        f"/api/v1/concerts/{sample_data['concert_id']}/setlist/songs",
        params={"song_id": sample_data['song2_id']}
    )
    
    # Verify setlist
    response = client.get(f"/api/v1/concerts/{sample_data['concert_id']}/setlist")
    data = response.json()
    assert len(data["songs"]) == 2
    assert data["total_duration_minutes"] == 7.0


def test_add_duplicate_song_to_setlist(sample_data):
    # Add song
    client.post(
        f"/api/v1/concerts/{sample_data['concert_id']}/setlist/songs",
        params={"song_id": sample_data['song1_id']}
    )
    
    # Try to add same song again
    response = client.post(
        f"/api/v1/concerts/{sample_data['concert_id']}/setlist/songs",
        params={"song_id": sample_data['song1_id']}
    )
    assert response.status_code == 400


def test_get_setlist_nonexistent_concert():
    response = client.get("/api/v1/concerts/999/setlist")
    assert response.status_code == 404


def test_clone_setlist(sample_data):
    # Create second concert
    concert_data = {
        "date": "2024-12-26T19:00:00",
        "venue_id": sample_data["venue_id"],
        "ticket_price": 60.0
    }
    concert_response = client.post("/api/v1/concerts", json=concert_data)
    target_concert_id = concert_response.json()["id"]
    
    # Add songs to source setlist
    client.post(
        f"/api/v1/concerts/{sample_data['concert_id']}/setlist/songs",
        params={"song_id": sample_data['song1_id']}
    )
    client.post(
        f"/api/v1/concerts/{sample_data['concert_id']}/setlist/songs",
        params={"song_id": sample_data['song2_id']}
    )
    
    # Clone setlist
    response = client.post(
        f"/api/v1/concerts/{target_concert_id}/setlist/clone/{sample_data['concert_id']}"
    )
    assert response.status_code == 200
    
    # Verify cloned setlist
    cloned_response = client.get(f"/api/v1/concerts/{target_concert_id}/setlist")
    cloned_data = cloned_response.json()
    assert len(cloned_data["songs"]) == 2
    assert cloned_data["total_duration_minutes"] == 7.0


def test_clone_to_concert_with_existing_setlist(sample_data):
    # Create second concert
    concert_data = {
        "date": "2024-12-26T19:00:00",
        "venue_id": sample_data["venue_id"]
    }
    concert_response = client.post("/api/v1/concerts", json=concert_data)
    target_concert_id = concert_response.json()["id"]
    
    # Add song to target concert first
    client.post(
        f"/api/v1/concerts/{target_concert_id}/setlist/songs",
        params={"song_id": sample_data['song1_id']}
    )
    
    # Try to clone
    response = client.post(
        f"/api/v1/concerts/{target_concert_id}/setlist/clone/{sample_data['concert_id']}"
    )
    assert response.status_code == 400
