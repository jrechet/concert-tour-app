"""Realistic multi-concert tour fixture data for future dashboard tests.

There is no dashboard feature on `main` yet and no persisted Concert model
(only the `ConcertCreate`/`ConcertResponse` Pydantic schemas exist) — so this
module seeds Tours through the real, already-working `/api/v1/tours/` API and
builds validated `ConcertCreate` objects in memory rather than writing to a
concerts table that doesn't exist. Concert dates are generated relative to
`base_time` (default: now) so the "must be in the future" validator always
passes, regardless of when a test runs.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from src.schemas.concert import ConcertCreate

_TOUR_TEMPLATES = [
    {
        "name": "Neon Skyline Tour",
        "artist": "Aurora Belle",
        "description": "A synth-pop arena tour spanning three continents.",
        "status": "active",
        "start_offset_days": 10,
        "end_offset_days": 70,
        "concerts": [
            {"venue": "Madison Square Garden", "city": "New York", "country": "USA",
             "day_offset": 15, "ticket_price": "125.00", "capacity": 20000},
            {"venue": "The O2 Arena", "city": "London", "country": "UK",
             "day_offset": 28, "ticket_price": "110.00", "capacity": 18000},
            {"venue": "Accor Arena", "city": "Paris", "country": "France",
             "day_offset": 35, "ticket_price": "115.00", "capacity": 15000},
            {"venue": "Tokyo Dome", "city": "Tokyo", "country": "Japan",
             "day_offset": 55, "ticket_price": "140.00", "capacity": 42000},
        ],
    },
    {
        "name": "Homecoming Revival Tour",
        "artist": "The Midnight Collective",
        "description": "A career-spanning tour celebrating a decade together.",
        "status": "planned",
        "start_offset_days": 40,
        "end_offset_days": 120,
        "concerts": [
            {"venue": "United Center", "city": "Chicago", "country": "USA",
             "day_offset": 45, "ticket_price": "95.00", "capacity": 23500},
            {"venue": "Scotiabank Arena", "city": "Toronto", "country": "Canada",
             "day_offset": 60, "ticket_price": "98.00", "capacity": 19800},
            {"venue": "Crypto.com Arena", "city": "Los Angeles", "country": "USA",
             "day_offset": 80, "ticket_price": "150.00", "capacity": 20000},
        ],
    },
    {
        "name": "River Stone Live",
        "artist": "River Stone",
        "description": "An intimate acoustic run through mid-size theaters.",
        "status": "planned",
        "start_offset_days": 5,
        "end_offset_days": 45,
        "concerts": [
            {"venue": "Ryman Auditorium", "city": "Nashville", "country": "USA",
             "day_offset": 7, "ticket_price": "65.00", "capacity": 2362},
            {"venue": "Red Rocks Amphitheatre", "city": "Morrison", "country": "USA",
             "day_offset": 20, "ticket_price": "89.00", "capacity": 9525},
            {"venue": "Massey Hall", "city": "Toronto", "country": "Canada",
             "day_offset": 33, "ticket_price": "70.00", "capacity": 2765},
            {"venue": "Sydney Opera House", "city": "Sydney", "country": "Australia",
             "day_offset": 44, "ticket_price": "99.00", "capacity": 2679},
        ],
    },
]


def build_multi_concert_tour_fixtures(base_time=None):
    """Build realistic tour + concert payloads anchored to `base_time` (default: now).

    Returns a list of dicts shaped like:
        {"tour": <TourCreate-compatible dict>, "concerts": [<raw concert dict>, ...]}
    Concert dicts still need a `tour_id` before they can become a validated
    `ConcertCreate` — see `attach_tour_ids`.
    """
    base_time = base_time or datetime.now()
    fixtures = []
    for template in _TOUR_TEMPLATES:
        start_date = (base_time + timedelta(days=template["start_offset_days"])).date()
        end_date = (base_time + timedelta(days=template["end_offset_days"])).date()
        tour = {
            "name": template["name"],
            "artist": template["artist"],
            "description": template["description"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": template["status"],
        }
        concerts = [
            {
                "venue": concert["venue"],
                "city": concert["city"],
                "country": concert["country"],
                "date_time": base_time + timedelta(days=concert["day_offset"]),
                "ticket_price": Decimal(concert["ticket_price"]),
                "capacity": concert["capacity"],
            }
            for concert in template["concerts"]
        ]
        fixtures.append({"tour": tour, "concerts": concerts})
    return fixtures


def attach_tour_ids(fixtures, tour_ids):
    """Pair each fixture's concert templates with a persisted tour id.

    `tour_ids` must line up in order with `fixtures`. Returns a list of dicts:
        {"tour_id": int, "concerts": [ConcertCreate, ...]}
    """
    seeded = []
    for fixture, tour_id in zip(fixtures, tour_ids):
        concerts = [
            ConcertCreate(**{**concert, "tour_id": tour_id})
            for concert in fixture["concerts"]
        ]
        seeded.append({"tour_id": tour_id, "concerts": concerts})
    return seeded


def compute_dashboard_stats(seeded_tours):
    """Aggregate stats a dashboard would show, computed from seeded fixture data."""
    total_concerts = sum(len(entry["concerts"]) for entry in seeded_tours)
    total_capacity = sum(
        concert.capacity or 0
        for entry in seeded_tours
        for concert in entry["concerts"]
    )
    projected_revenue = sum(
        (concert.ticket_price or Decimal("0")) * (concert.capacity or 0)
        for entry in seeded_tours
        for concert in entry["concerts"]
    )
    countries = sorted({
        concert.country
        for entry in seeded_tours
        for concert in entry["concerts"]
    })
    return {
        "total_tours": len(seeded_tours),
        "total_concerts": total_concerts,
        "total_capacity": total_capacity,
        "projected_revenue": projected_revenue,
        "countries": countries,
    }
