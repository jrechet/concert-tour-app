"""Unit tests for `build_tour_calendar`."""

from datetime import datetime

from icalendar import Calendar

from src.services.calendar_service import build_tour_calendar
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestBuildTourCalendar:
    """Coverage for `build_tour_calendar`."""

    def test_tour_with_n_concerts_produces_n_vevents(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        for i, venue in enumerate(venues):
            create_concert(db_session, tour, venue, day_offset=i, ticket_price="80.00", base_time=BASE_TIME)
        db_session.refresh(tour)

        ics_bytes = build_tour_calendar(tour)
        parsed = Calendar.from_ical(ics_bytes)
        vevents = [component for component in parsed.walk() if component.name == "VEVENT"]

        assert len(vevents) == 3

    def test_each_vevent_summary_contains_city_and_location_contains_venue(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        for i, venue in enumerate(venues):
            create_concert(db_session, tour, venue, day_offset=i, ticket_price="80.00", base_time=BASE_TIME)
        db_session.refresh(tour)

        ics_bytes = build_tour_calendar(tour)
        parsed = Calendar.from_ical(ics_bytes)
        vevents = [component for component in parsed.walk() if component.name == "VEVENT"]

        assert len(vevents) == len(venues)
        for vevent, venue in zip(vevents, venues):
            assert venue.city in str(vevent.get("summary"))
            assert venue.name in str(vevent.get("location"))

    def test_uid_is_stable_and_derived_from_concert_id(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        db_session.refresh(tour)

        ics_bytes = build_tour_calendar(tour)
        parsed = Calendar.from_ical(ics_bytes)
        vevent = [component for component in parsed.walk() if component.name == "VEVENT"][0]

        assert str(vevent.get("uid")) == f"concert-{concert.id}@concert-tour-app"

    def test_calendar_has_prodid_and_calscale(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )
        db_session.refresh(tour)

        ics_bytes = build_tour_calendar(tour)
        parsed = Calendar.from_ical(ics_bytes)

        assert parsed.get("prodid") is not None
        assert str(parsed.get("calscale")) == "GREGORIAN"

    def test_empty_tour_produces_zero_vevents(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )
        db_session.refresh(tour)

        ics_bytes = build_tour_calendar(tour)
        parsed = Calendar.from_ical(ics_bytes)
        vevents = [component for component in parsed.walk() if component.name == "VEVENT"]

        assert vevents == []

    def test_midnight_date_time_produces_all_day_event(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=datetime(2024, 6, 15, 0, 0, 0),
        )
        db_session.refresh(tour)

        ics_bytes = build_tour_calendar(tour)
        parsed = Calendar.from_ical(ics_bytes)
        vevent = [component for component in parsed.walk() if component.name == "VEVENT"][0]

        assert vevent.get("dtstart").dt == concert.date_time.date()

    def test_time_component_produces_timed_event(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        db_session.refresh(tour)

        ics_bytes = build_tour_calendar(tour)
        parsed = Calendar.from_ical(ics_bytes)
        vevent = [component for component in parsed.walk() if component.name == "VEVENT"][0]

        dtstart = vevent.get("dtstart").dt
        assert dtstart.hour == BASE_TIME.hour
        assert dtstart.tzinfo is not None
