import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_read_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Concert Tour API is running"}


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_app_startup():
    """Test that the FastAPI app can be created and started"""
    assert app is not None
    assert app.title == "Concert Tour API"
    assert app.description == "API for managing concert tours and events"
    assert app.version == "1.0.0"
