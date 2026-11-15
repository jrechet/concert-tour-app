"""Unit tests for `update_venue`."""

import pytest

from src.schemas.venue import VenueUpdate
from src.services.venue_service import VenueConflictError, VenueNotFoundError, update_venue
from tests.fixtures.dashboard_fixtures import create_venues


class TestUpdateVenue:
    """Coverage for `update_venue`."""

    def test_updates_name_only_and_leaves_other_fields_untouched(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = update_venue(db_session, venue.id, VenueUpdate(name="New Name"))

        assert result.name == "New Name"
        assert result.city == venue.city
        assert result.country == venue.country
        assert result.capacity == venue.capacity

    def test_updates_city_only_and_leaves_other_fields_untouched(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = update_venue(db_session, venue.id, VenueUpdate(city="New City"))

        assert result.city == "New City"
        assert result.name == venue.name
        assert result.country == venue.country
        assert result.capacity == venue.capacity

    def test_updates_country_only_and_leaves_other_fields_untouched(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = update_venue(db_session, venue.id, VenueUpdate(country="New Country"))

        assert result.country == "New Country"
        assert result.name == venue.name
        assert result.city == venue.city
        assert result.capacity == venue.capacity

    def test_updates_capacity_only_and_leaves_other_fields_untouched(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = update_venue(db_session, venue.id, VenueUpdate(capacity=99999))

        assert result.capacity == 99999
        assert result.name == venue.name
        assert result.city == venue.city
        assert result.country == venue.country

    def test_raises_not_found_for_unknown_venue_id(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        unknown_venue_id = venue.id + 1

        while db_session.query(type(venue)).filter(type(venue).id == unknown_venue_id).first() is not None:
            unknown_venue_id += 1

        with pytest.raises(VenueNotFoundError):
            update_venue(db_session, unknown_venue_id, VenueUpdate(name="Doesn't Matter"))

    def test_combined_name_and_city_collision_raises_conflict(self, db_session):
        venue, other_venue = create_venues(db_session, count=2)

        with pytest.raises(VenueConflictError):
            update_venue(
                db_session,
                venue.id,
                VenueUpdate(name=other_venue.name, city=other_venue.city),
            )

    def test_name_only_change_that_collides_with_venues_existing_city_raises_conflict(self, db_session):
        venue, other_venue = create_venues(db_session, count=2)
        other_venue.city = venue.city
        db_session.commit()

        with pytest.raises(VenueConflictError):
            update_venue(db_session, venue.id, VenueUpdate(name=other_venue.name))

    def test_city_only_change_that_collides_with_venues_existing_name_raises_conflict(self, db_session):
        venue, other_venue = create_venues(db_session, count=2)
        other_venue.name = venue.name
        db_session.commit()

        with pytest.raises(VenueConflictError):
            update_venue(db_session, venue.id, VenueUpdate(city=other_venue.city))

    def test_renaming_venue_to_its_own_current_name_in_its_own_city_is_not_a_conflict(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = update_venue(db_session, venue.id, VenueUpdate(name=venue.name, city=venue.city))

        assert result.name == venue.name
        assert result.city == venue.city

    def test_same_name_different_city_remains_valid(self, db_session):
        venue, other_venue = create_venues(db_session, count=2)

        result = update_venue(db_session, venue.id, VenueUpdate(name=other_venue.name))

        assert result.name == other_venue.name
        assert result.city == venue.city
