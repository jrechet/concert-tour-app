"""Tests for `duplicate_tour`."""

from datetime import datetime

from src.models import Concert, Tour
from src.services.tour_service import duplicate_tour
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2025, 6, 1, 20, 0, 0)


class TestDuplicateTour:
    """Coverage for `duplicate_tour`."""

    def test_happy_path_copies_fields_with_new_id_planned_status_and_no_concerts(self, db_session):
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active", description="A synth-pop arena tour.",
        )

        result = duplicate_tour(db_session, source.id)

        assert result is not None
        assert result.id != source.id
        assert result.artist == source.artist
        assert result.name == "Neon Skyline World Tour (copy)"
        assert result.status == "planned"
        assert result.start_date == source.start_date
        assert result.end_date == source.end_date
        assert result.description == source.description
        assert list(result.concerts) == []

    def test_source_tour_is_left_unmodified(self, db_session):
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active", description="A synth-pop arena tour.",
        )

        duplicate_tour(db_session, source.id)

        db_session.refresh(source)
        assert source.name == "Neon Skyline World Tour"
        assert source.status == "active"
        assert list(source.concerts) == []

    def test_source_with_concerts_keeps_them_and_copy_gets_none(self, db_session):
        venues = create_venues(db_session, count=2)
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, source, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, source, venues[1], day_offset=1, ticket_price="90.00", base_time=BASE_TIME)

        result = duplicate_tour(db_session, source.id)

        db_session.refresh(source)
        assert db_session.query(Concert).filter(Concert.tour_id == source.id).count() == 2
        assert db_session.query(Concert).filter(Concert.tour_id == result.id).count() == 0

    def test_unknown_tour_id_returns_none_and_writes_nothing(self, db_session):
        result = duplicate_tour(db_session, 999999)

        assert result is None
        assert db_session.query(Tour).count() == 0

    def test_duplicating_a_copy_applies_suffix_again_without_deduplicating(self, db_session):
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )

        first_copy = duplicate_tour(db_session, source.id)
        second_copy = duplicate_tour(db_session, first_copy.id)

        assert first_copy.name == "Neon Skyline World Tour (copy)"
        assert second_copy.name == "Neon Skyline World Tour (copy) (copy)"
