"""ORM-backed dashboard test fixtures: tours, venues, and concerts.

`tests/fixtures/dashboard_data.py` predates the persisted `Concert`/`Venue`
models and seeds tours through the API with in-memory `ConcertCreate`
payloads. This module builds on the `Venue` and `Concert` SQLAlchemy models
and persists everything through a real ORM session, so every foreign key
(`Concert.tour_id`, `Concert.venue_id`) is a real id from a committed row
rather than a hardcoded literal like `venue_id=1`.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from src.models import Concert, Tour, Venue

_VENUE_TEMPLATES = [
    {"name": "Madison Square Garden", "city": "New York", "country": "USA", "capacity": 20000},
    {"name": "The O2 Arena", "city": "London", "country": "UK", "capacity": 18000},
    {"name": "Accor Arena", "city": "Paris", "country": "France", "capacity": 15000},
    {"name": "Tokyo Dome", "city": "Tokyo", "country": "Japan", "capacity": 42000},
    {"name": "United Center", "city": "Chicago", "country": "USA", "capacity": 23500},
    {"name": "Scotiabank Arena", "city": "Toronto", "country": "Canada", "capacity": 19800},
    {"name": "Crypto.com Arena", "city": "Los Angeles", "country": "USA", "capacity": 20000},
    {"name": "Red Rocks Amphitheatre", "city": "Morrison", "country": "USA", "capacity": 9525},
    {"name": "Sydney Opera House", "city": "Sydney", "country": "Australia", "capacity": 2679},
    {"name": "Massey Hall", "city": "Toronto", "country": "Canada", "capacity": 2765},
    {"name": "Ryman Auditorium", "city": "Nashville", "country": "USA", "capacity": 2362},
]


def create_venues(db_session, count=None):
    """Persist and return distinct `Venue` rows."""
    templates = _VENUE_TEMPLATES[:count] if count else _VENUE_TEMPLATES
    venues = [Venue(**template) for template in templates]
    db_session.add_all(venues)
    db_session.commit()
    for venue in venues:
        db_session.refresh(venue)
    return venues


def create_tour(db_session, name, artist, start_date, end_date, status, description=""):
    """Persist and return a `Tour` row."""
    tour = Tour(
        name=name,
        artist=artist,
        start_date=start_date,
        end_date=end_date,
        status=status,
        description=description,
    )
    db_session.add(tour)
    db_session.commit()
    db_session.refresh(tour)
    return tour


def create_concert(db_session, tour, venue, day_offset, ticket_price, base_time):
    """Persist and return a `Concert` linked to a real tour and venue via FK."""
    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=base_time + timedelta(days=day_offset),
        ticket_price=Decimal(ticket_price),
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


def build_full_tour_with_concerts(db_session, base_time=None):
    """A tour with 11 concerts spanning past, present, and future dates,
    cycled across 8 distinct venues (some cities are revisited, as real
    tours often do).
    """
    base_time = base_time or datetime.now()
    venues = create_venues(db_session, count=8)
    tour = create_tour(
        db_session,
        name="Neon Skyline World Tour",
        artist="Aurora Belle",
        start_date=(base_time - timedelta(days=60)).date(),
        end_date=(base_time + timedelta(days=90)).date(),
        status="active",
        description="A synth-pop arena tour spanning three continents.",
    )
    day_offsets = [-45, -30, -15, -3, -1, 0, 2, 10, 25, 40, 60]
    concerts = [
        create_concert(
            db_session,
            tour,
            venues[i % len(venues)],
            offset,
            ticket_price=f"{80 + i * 5}.00",
            base_time=base_time,
        )
        for i, offset in enumerate(day_offsets)
    ]
    return {"tour": tour, "venues": venues, "concerts": concerts}


def build_empty_tour(db_session, base_time=None):
    """A tour with zero concerts (empty state)."""
    base_time = base_time or datetime.now()
    tour = create_tour(
        db_session,
        name="Unannounced Tour",
        artist="TBD Collective",
        start_date=(base_time + timedelta(days=120)).date(),
        end_date=(base_time + timedelta(days=150)).date(),
        status="planned",
        description="Dates not yet announced.",
    )
    return {"tour": tour, "venues": [], "concerts": []}


def build_future_only_tour(db_session, base_time=None):
    """A tour where every concert is scheduled in the future (no completed
    shows yet).
    """
    base_time = base_time or datetime.now()
    venues = create_venues(db_session, count=4)
    tour = create_tour(
        db_session,
        name="Homecoming Revival Tour",
        artist="The Midnight Collective",
        start_date=(base_time + timedelta(days=10)).date(),
        end_date=(base_time + timedelta(days=90)).date(),
        status="planned",
        description="A career-spanning tour celebrating a decade together.",
    )
    day_offsets = [15, 30, 50, 75]
    concerts = [
        create_concert(
            db_session, tour, venues[i % len(venues)], offset, ticket_price="95.00", base_time=base_time
        )
        for i, offset in enumerate(day_offsets)
    ]
    return {"tour": tour, "venues": venues, "concerts": concerts}


def build_past_only_tour(db_session, base_time=None):
    """A tour that is fully completed — every concert is in the past."""
    base_time = base_time or datetime.now()
    venues = create_venues(db_session, count=4)
    tour = create_tour(
        db_session,
        name="River Stone Farewell Tour",
        artist="River Stone",
        start_date=(base_time - timedelta(days=120)).date(),
        end_date=(base_time - timedelta(days=30)).date(),
        status="completed",
        description="An intimate acoustic run through mid-size theaters.",
    )
    day_offsets = [-110, -90, -60, -35]
    concerts = [
        create_concert(
            db_session, tour, venues[i % len(venues)], offset, ticket_price="65.00", base_time=base_time
        )
        for i, offset in enumerate(day_offsets)
    ]
    return {"tour": tour, "venues": venues, "concerts": concerts}
