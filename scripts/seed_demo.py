"""Demo data for the swarm's QA walk (`demo.seed` in theswarm.yaml).

The swarm demos every cycle on a server started from a fresh workspace, and
its database was empty: the dashboard showed nothing, and a page a cycle
added (GET /api/v1/concerts/1/occupancy) answered 404 and never reached the
demo. This fills an empty database with a small, believable tour schedule —
dates relative to today, so "upcoming" stays true — and leaves a database
that already has tours alone.

    python scripts/seed_demo.py            # the database of DATABASE_URL
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Base, Concert, LineupEntry, Tour, Venue  # noqa: E402

VENUES = [
    ("Madison Square Garden", "New York", "USA", 20000),
    ("The O2 Arena", "London", "UK", 18000),
    ("Accor Arena", "Paris", "France", 15000),
    ("Ryman Auditorium", "Nashville", "USA", 2362),
    ("Paradiso", "Amsterdam", "Netherlands", None),  # capacity unknown
]

# (tour, artist, status, description, [(venue index, days from now, price, tickets sold)])
TOURS = [
    ("Neon Skyline Tour", "Aurora Belle", "active",
     "A synth-pop arena tour spanning three continents.",
     [(0, 12, "125.00", 15000), (1, 26, "110.00", 18000), (2, 40, "115.00", 9100)]),
    ("River Stone Live", "River Stone", "planned",
     "An intimate acoustic run through mid-size theaters.",
     [(3, 8, "65.00", 2200), (4, 21, "45.00", 480)]),
    ("Homecoming Revival Tour", "The Midnight Collective", "completed",
     "A career-spanning tour celebrating a decade together.",
     [(0, -30, "95.00", 19500)]),
]

LINEUP = ["Glass Harbor", "June Static"]  # the support acts of the first concert


def seed(session, today: date | None = None) -> bool:
    """Fill an empty database; True when it wrote, False when tours exist."""
    if session.query(Tour).count():
        return False
    today = today or date.today()
    venues = [Venue(name=n, city=c, country=k, capacity=cap) for n, c, k, cap in VENUES]
    session.add_all(venues)
    session.flush()
    first_concert = None
    for name, artist, status, description, dates in TOURS:
        offsets = [days for _, days, _, _ in dates]
        tour = Tour(
            name=name, artist=artist, status=status, description=description,
            start_date=today + timedelta(days=min(offsets) - 2),
            end_date=today + timedelta(days=max(offsets) + 2),
        )
        session.add(tour)
        session.flush()
        for venue_index, days, price, sold in dates:
            concert = Concert(
                tour_id=tour.id, venue=venues[venue_index],
                date_time=datetime.combine(today + timedelta(days=days), datetime.min.time()).replace(hour=20),
                ticket_price=Decimal(price),
            )
            concert.tickets_sold = sold
            session.add(concert)
            session.flush()
            first_concert = first_concert or concert
    for order, act in enumerate(LINEUP, start=1):
        session.add(LineupEntry(concert_id=first_concert.id, artist_name=act, set_order=order))
    session.commit()
    return True


def main() -> int:
    from src.database import SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        wrote = seed(session)
    finally:
        session.close()
    print("demo data written" if wrote else "demo data already there — left alone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
