"""Unit tests for the `TicketTierRead` Pydantic schema."""

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from src.models import TicketTier
from src.schemas.ticket_tier import TicketTierRead
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def test_serializes_plain_object_with_two_decimals():
    tier = SimpleNamespace(id=1, name="General Admission", price=Decimal("45"))

    read = TicketTierRead.model_validate(tier)

    assert read.id == 1
    assert read.name == "General Admission"
    assert read.price == Decimal("45.00")
    assert str(read.price) == "45.00"


def test_rounds_to_two_decimals_when_given_more_precision():
    tier = SimpleNamespace(id=1, name="VIP", price=Decimal("119.995"))

    read = TicketTierRead.model_validate(tier)

    assert str(read.price) == "120.00"


def test_round_trips_from_real_orm_instance(db_session):
    base_time = datetime(2026, 11, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=base_time.date(),
        end_date=(base_time + timedelta(days=10)).date(),
        status="planned",
    )
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )
    tier = TicketTier(concert_id=concert.id, name="General Admission", price=Decimal("45.5"))
    db_session.add(tier)
    db_session.commit()
    db_session.refresh(tier)

    read = TicketTierRead.model_validate(tier)

    assert read.id == tier.id
    assert read.name == "General Admission"
    assert str(read.price) == "45.50"
