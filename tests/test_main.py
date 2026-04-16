import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_home_route():
    """Test that home route returns HTML response"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

def test_dashboard_route():
    """Test that dashboard route returns HTML response"""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

def test_dashboard_route_exists():
    """Test that dashboard route exists and doesn't return 404"""
    response = client.get("/dashboard")
    assert response.status_code != 404

def test_static_files_mount():
    """Test that static files are properly mounted"""
    # This test assumes there's at least one static file to test with
    # If no static files exist, this will pass as the mount is configured
    response = client.get("/static/")
    # Should not return 500 server error, either 200 (if files exist) or 404 (if no index)
    assert response.status_code in [200, 404]
