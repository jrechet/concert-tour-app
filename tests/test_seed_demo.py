"""The demo seed fills an empty database once, with upcoming dates."""

from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from scripts.seed_demo import seed
from src.models import Base, Concert, LineupEntry, Tour
from src.services.concerts_service import get_concert_occupancy


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_an_empty_database_gets_tours_concerts_and_a_lineup():
    session = _session()

    assert seed(session, today=date(2026, 9, 28)) is True

    assert session.query(Tour).count() == 3
    assert session.query(Concert).count() == 6
    assert session.query(LineupEntry).filter_by(concert_id=1).count() == 2
    upcoming = session.query(Concert).filter(Concert.date_time > datetime(2026, 9, 28)).count()
    assert upcoming == 5


def test_a_database_with_tours_is_left_alone():
    session = _session()
    seed(session)

    assert seed(session) is False
    assert session.query(Tour).count() == 3


def test_the_first_concert_has_an_occupancy_to_show():
    session = _session()
    seed(session)

    occupancy = get_concert_occupancy(session, 1)

    assert occupancy is not None
    assert occupancy.tickets_sold == 15000 and occupancy.percentage_sold == 75.0
