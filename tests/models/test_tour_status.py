"""Tests for the `TourStatus.PLANNED` member's public surface and its
round-trip through a real database insert/select."""

from datetime import date

from src.models.tour import Tour
from src.schemas.tour import TourStatus


def test_planned_member_is_importable_and_lowercase():
    assert TourStatus.PLANNED.value == "planned"


def test_planned_status_round_trips_through_the_database(db_session):
    tour = Tour(
        name="Round Trip Tour",
        artist="The Testers",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        status=TourStatus.PLANNED.value,
    )
    db_session.add(tour)
    db_session.commit()

    persisted = db_session.query(Tour).filter(Tour.id == tour.id).first()

    assert persisted is not None
    assert TourStatus(persisted.status) is TourStatus.PLANNED
