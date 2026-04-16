"""Test configuration and fixtures."""

import pytest
from app import create_app, db
from models import Song, Setlist


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_songs(app):
    """Create sample songs for testing."""
    songs = [
        Song(title="Song One", artist="Artist A", duration=210),
        Song(title="Song Two", artist="Artist B", duration=180),
        Song(title="Song Three", artist="Artist C", duration=240),
        Song(title="Song Four", artist="Artist A", duration=195),
        Song(title="Song Five", artist="Artist D", duration=220),
    ]
    
    for song in songs:
        db.session.add(song)
    db.session.commit()
    
    return songs


@pytest.fixture
def sample_setlist(app, sample_songs):
    """Create a sample setlist for testing."""
    setlist = Setlist(name="Test Setlist")
    db.session.add(setlist)
    db.session.flush()
    
    # Add first 3 songs to setlist
    for i, song in enumerate(sample_songs[:3]):
        setlist.add_song(song, order_position=i)
    
    db.session.commit()
    return setlist
