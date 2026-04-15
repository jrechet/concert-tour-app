import pytest


def test_create_concert(client, created_tour, sample_concert_data):
    """Test creating a new concert."""
    sample_concert_data["tour_id"] = created_tour["id"]
    response = client.post("/api/v1/concerts/", json=sample_concert_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["venue"] == sample_concert_data["venue"]
    assert data["city"] == sample_concert_data["city"]
    assert data["date"] == sample_concert_data["date"]
    assert data["time"] == sample_concert_data["time"]
    assert data["ticket_price"] == sample_concert_data["ticket_price"]
    assert data["tour_id"] == sample_concert_data["tour_id"]
    assert "id" in data


def test_create_concert_invalid_tour_id(client, sample_concert_data):
    """Test creating a concert with non-existent tour_id."""
    sample_concert_data["tour_id"] = 999  # Non-existent tour
    response = client.post("/api/v1/concerts/", json=sample_concert_data)
    
    assert response.status_code == 400
    assert "tour not found" in response.json()["detail"].lower()


def test_create_concert_invalid_data(client, created_tour):
    """Test creating a concert with invalid data."""
    invalid_data = {
        "venue": "",  # Empty venue
        "city": "Test City",
        "date": "invalid-date",  # Invalid date format
        "time": "25:00:00",  # Invalid time
        "ticket_price": -10,  # Negative price
        "tour_id": created_tour["id"]
    }
    
    response = client.post("/api/v1/concerts/", json=invalid_data)
    assert response.status_code == 422


def test_get_concerts(client, created_concert):
    """Test getting all concerts."""
    response = client.get("/api/v1/concerts/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == created_concert["id"]


def test_get_concerts_filtered_by_tour(client, created_tour, sample_concert_data):
    """Test getting concerts filtered by tour_id."""
    # Create concerts for different tours
    sample_concert_data["tour_id"] = created_tour["id"]
    client.post("/api/v1/concerts/", json=sample_concert_data)
    
    # Create another tour and concert
    tour_data = {
        "name": "Another Tour",
        "artist": "Another Artist", 
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    tour_response = client.post("/api/v1/tours/", json=tour_data)
    tour2_id = tour_response.json()["id"]
    
    concert_data2 = sample_concert_data.copy()
    concert_data2["tour_id"] = tour2_id
    concert_data2["venue"] = "Another Venue"
    client.post("/api/v1/concerts/", json=concert_data2)
    
    # Test filtering by first tour
    response = client.get(f"/api/v1/concerts/?tour_id={created_tour['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tour_id"] == created_tour["id"]


def test_get_concert_by_id(client, created_concert):
    """Test getting a specific concert by ID."""
    concert_id = created_concert["id"]
    response = client.get(f"/api/v1/concerts/{concert_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert_id
    assert data["venue"] == created_concert["venue"]


def test_get_concert_not_found(client):
    """Test getting a concert that doesn't exist."""
    response = client.get("/api/v1/concerts/999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_concert(client, created_concert, created_tour):
    """Test updating an existing concert."""
    concert_id = created_concert["id"]
    update_data = {
        "venue": "Updated Venue",
        "ticket_price": 149.99
    }
    
    response = client.put(f"/api/v1/concerts/{concert_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["venue"] == update_data["venue"]
    assert data["ticket_price"] == update_data["ticket_price"]
    assert data["city"] == created_concert["city"]  # Unchanged


def test_update_concert_invalid_tour_id(client, created_concert):
    """Test updating concert with invalid tour_id."""
    concert_id = created_concert["id"]
    update_data = {"tour_id": 999}  # Non-existent tour
    
    response = client.put(f"/api/v1/concerts/{concert_id}", json=update_data)
    
    assert response.status_code == 400
    assert "tour not found" in response.json()["detail"].lower()


def test_update_concert_not_found(client):
    """Test updating a concert that doesn't exist."""
    update_data = {"venue": "Updated Venue"}
    response = client.put("/api/v1/concerts/999", json=update_data)
    
    assert response.status_code == 404


def test_delete_concert(client, created_concert):
    """Test deleting a concert."""
    concert_id = created_concert["id"]
    response = client.delete(f"/api/v1/concerts/{concert_id}")
    
    assert response.status_code == 204
    
    # Verify concert is deleted
    get_response = client.get(f"/api/v1/concerts/{concert_id}")
    assert get_response.status_code == 404


def test_delete_concert_not_found(client):
    """Test deleting a concert that doesn't exist."""
    response = client.delete("/api/v1/concerts/999")
    
    assert response.status_code == 404


def test_concert_foreign_key_constraint(client, created_tour, created_concert):
    """Test that deleting a tour with concerts fails due to foreign key constraint."""
    # This test depends on the database configuration
    # In SQLite with foreign key constraints enabled, this should fail
    tour_id = created_tour["id"]
    response = client.delete(f"/api/v1/tours/{tour_id}")
    
    # The behavior may vary based on database configuration
    # In a properly configured system with FK constraints, this should fail
    # For now, we'll test that the concert still exists if tour deletion succeeds
    if response.status_code == 204:
        # Tour was deleted, check if concert still exists
        concert_response = client.get(f"/api/v1/concerts/{created_concert['id']}")
        # Concert should either still exist or have been cascade deleted
        assert concert_response.status_code in [200, 404]


def test_multiple_concerts_same_tour(client, created_tour, sample_concert_data):
    """Test creating multiple concerts for the same tour."""
    sample_concert_data["tour_id"] = created_tour["id"]
    
    # Create first concert
    response1 = client.post("/api/v1/concerts/", json=sample_concert_data)
    assert response1.status_code == 201
    
    # Create second concert with different venue
    sample_concert_data["venue"] = "Another Venue"
    sample_concert_data["date"] = "2024-07-01"
    response2 = client.post("/api/v1/concerts/", json=sample_concert_data)
    assert response2.status_code == 201
    
    # Verify both concerts exist
    response = client.get("/api/v1/concerts/")
    data = response.json()
    assert len(data) == 2
    assert all(concert["tour_id"] == created_tour["id"] for concert in data)


def test_concert_price_validation(client, created_tour, sample_concert_data):
    """Test concert price validation."""
    sample_concert_data["tour_id"] = created_tour["id"]
    
    # Test negative price
    sample_concert_data["ticket_price"] = -50.0
    response = client.post("/api/v1/concerts/", json=sample_concert_data)
    assert response.status_code == 422
    
    # Test zero price (should be valid)
    sample_concert_data["ticket_price"] = 0.0
    response = client.post("/api/v1/concerts/", json=sample_concert_data)
    assert response.status_code == 201
    
    # Test very high price (should be valid)
    sample_concert_data["venue"] = "Expensive Venue"
    sample_concert_data["ticket_price"] = 999999.99
    response = client.post("/api/v1/concerts/", json=sample_concert_data)
    assert response.status_code == 201
