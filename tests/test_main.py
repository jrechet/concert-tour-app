from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "message": "Concert Tour App is running"}


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Concert Tour App"}


def test_app_startup():
    """Test that the app starts without errors"""
    assert app.title == "Concert Tour App"
    assert app.version == "1.0.0"
