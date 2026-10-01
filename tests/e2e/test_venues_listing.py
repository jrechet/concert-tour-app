"""End-to-end coverage: boots the real app, seeds venues via the ORM, and
exercises `GET /api/v1/venues` against a realistic multi-city dataset."""

from src.models import Venue


def seed_venues(db_session):
    """Persist a realistic set of venues spanning several cities/capacities."""
    venues = [
        Venue(name="Madison Square Garden", city="New York", country="USA", capacity=20000),
        Venue(name="The O2 Arena", city="London", country="UK", capacity=18000),
        Venue(name="Accor Arena", city="Paris", country="France", capacity=15000),
        Venue(name="Budokan", city="Tokyo", country="Japan", capacity=14471),
    ]
    db_session.add_all(venues)
    db_session.commit()
    for venue in venues:
        db_session.refresh(venue)
    return venues


class TestVenuesListingEndToEnd:
    """Boots the app and exercises `/api/v1/venues` end-to-end."""

    def test_list_without_min_capacity_returns_all_venues_sorted_by_name(self, client, db_session):
        seed_venues(db_session)

        response = client.get("/api/v1/venues")

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == [
            "Accor Arena", "Budokan", "Madison Square Garden", "The O2 Arena",
        ]
        assert data[0] == {
            "name": "Accor Arena",
            "city": "Paris",
            "country": "France",
            "capacity": 15000,
        }

    def test_list_with_min_capacity_filters_and_sorts(self, client, db_session):
        seed_venues(db_session)

        response = client.get("/api/v1/venues", params={"min_capacity": 15000})

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == [
            "Accor Arena", "Madison Square Garden", "The O2 Arena",
        ]
        assert all(venue["capacity"] >= 15000 for venue in data)

    def test_negative_min_capacity_returns_422(self, client, db_session):
        seed_venues(db_session)

        response = client.get("/api/v1/venues", params={"min_capacity": -1})

        assert response.status_code == 422

    def test_openapi_exposes_get_venues_with_venue_out_schema(self, client):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        spec = response.json()

        assert "/api/v1/venues" in spec["paths"]
        get_op = spec["paths"]["/api/v1/venues"]["get"]
        response_schema = get_op["responses"]["200"]["content"]["application/json"]["schema"]
        items_ref = response_schema["items"]["$ref"]
        assert items_ref == "#/components/schemas/VenueOut"
        assert "VenueOut" in spec["components"]["schemas"]
