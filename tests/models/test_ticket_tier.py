"""Tests for the `TicketTier` model: persistence against a real `Concert`
FK, the `Concert.tiers` relationship, cascade deletion, and model-level
validation of `price`/`name`."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.models import TicketTier
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session):
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
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )


def test_tier_persists_with_real_fk_to_concert(db_session):
    concert = _build_concert(db_session)
    tier = TicketTier(concert_id=concert.id, name="General Admission", price=Decimal("45.00"))
    db_session.add(tier)
    db_session.commit()
    db_session.refresh(tier)

    assert isinstance(tier.id, int)
    persisted = db_session.query(TicketTier).filter(TicketTier.id == tier.id).first()
    assert persisted.concert_id == concert.id
    assert persisted.name == "General Admission"
    assert persisted.price == Decimal("45.00")


def test_concert_tiers_returns_inserted_tiers(db_session):
    concert = _build_concert(db_session)
    db_session.add_all([
        TicketTier(concert_id=concert.id, name="General Admission", price=Decimal("45.00")),
        TicketTier(concert_id=concert.id, name="VIP", price=Decimal("120.00")),
    ])
    db_session.commit()
    db_session.refresh(concert)

    assert {tier.name for tier in concert.tiers} == {"General Admission", "VIP"}


def test_deleting_concert_cascades_to_tiers(db_session):
    concert = _build_concert(db_session)
    db_session.add(TicketTier(concert_id=concert.id, name="General Admission", price=Decimal("45.00")))
    db_session.commit()
    concert_id = concert.id

    db_session.delete(concert)
    db_session.commit()

    remaining = db_session.query(TicketTier).filter(TicketTier.concert_id == concert_id).count()
    assert remaining == 0


def test_negative_price_is_rejected(db_session):
    concert = _build_concert(db_session)

    with pytest.raises(ValueError):
        TicketTier(concert_id=concert.id, name="General Admission", price=Decimal("-1"))


def test_blank_name_is_rejected(db_session):
    concert = _build_concert(db_session)

    with pytest.raises(ValueError):
        TicketTier(concert_id=concert.id, name="", price=Decimal("10.00"))
