import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import get_db, Base
from src.models import Song

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_songs.db"
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


def test_create_song():
    song_data = {
        "title": "Test Song",
        "artist": "Test Artist",
        "duration_minutes": 3.5
    }
    response = client.post("/api/v1/songs", json=song_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Song"
    assert data["artist"] == "Test Artist"
    assert data["duration_minutes"] == 3.5
    assert "id" in data


def test_get_songs():
    # Create test songs
    song_data_1 = {"title": "Song 1", "artist": "Artist 1", "duration_minutes": 3.0}
    song_data_2 = {"title": "Song 2", "artist": "Artist 2", "duration_minutes": 4.0}
    
    client.post("/api/v1/songs", json=song_data_1)
    client.post("/api/v1/songs", json=song_data_2)
    
    response = client.get("/api/v1/songs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_song():
    # Create a song
    song_data = {"title": "Original Song", "artist": "Original Artist"}
    create_response = client.post("/api/v1/songs", json=song_data)
    song_id = create_response.json()["id"]
    
    # Update the song
    update_data = {"title": "Updated Song", "artist": "Updated Artist"}
    response = client.put(f"/api/v1/songs/{song_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Song"
    assert data["artist"] == "Updated Artist"


def test_update_nonexistent_song():
    update_data = {"title": "Updated Song"}
    response = client.put("/api/v1/songs/999", json=update_data)
    assert response.status_code == 404


def test_delete_song():
    # Create a song
    song_data = {"title": "Song to Delete", "artist": "Artist"}
    create_response = client.post("/api/v1/songs", json=song_data)
    song_id = create_response.json()["id"]
    
    # Delete the song
    response = client.delete(f"/api/v1/songs/{song_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get("/api/v1/songs")
    assert len(get_response.json()) == 0


def test_delete_nonexistent_song():
    response = client.delete("/api/v1/songs/999")
    assert response.status_code == 404
