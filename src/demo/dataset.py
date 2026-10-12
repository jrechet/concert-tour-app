"""Single source of truth for the "band builds and follows a tour" demo
scenario, shared by the seed script, the API, and the docs.

`build_demo_dataset` only builds Python objects in memory: it never opens a
database session and never makes an HTTP call, so callers decide how (or
whether) to persist the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from src.demo import config
from src.schemas.tour import TourStatus

# Day offsets (relative to `now`) applied to successive venues, chosen so a
# mix of already-happened and still-upcoming concerts shows up regardless of
# how many venues are configured.
_DAY_OFFSETS = [-30, 10, 25, 40, -5, 18]

# A pool of real-sounding venues to draw from, each in a different city.
_VENUE_POOL = [
    ("Madison Square Garden", "New York", "USA", 20000),
    ("The O2 Arena", "London", "UK", 18000),
    ("Accor Arena", "Paris", "France", 15000),
    ("Ryman Auditorium", "Nashville", "USA", 2362),
    ("Paradiso", "Amsterdam", "Netherlands", 1500),
    ("Nippon Budokan", "Tokyo", "Japan", 14471),
]


@dataclass(frozen=True)
class DemoBand:
    """The band behind the demo tour."""

    name: str


@dataclass(frozen=True)
class DemoVenue:
    """A venue hosting one stop of the demo tour."""

    name: str
    city: str
    country: str
    capacity: int


@dataclass(frozen=True)
class DemoTicketTier:
    """A priced ticket tier offered for a concert."""

    name: str
    price: Decimal


@dataclass(frozen=True)
class DemoConcert:
    """A single tour stop: a venue, a date, and its ticket tiers."""

    venue: DemoVenue
    date_time: datetime
    ticket_tiers: List[DemoTicketTier]


@dataclass(frozen=True)
class DemoTour:
    """The tour the demo band is currently following."""

    name: str
    band: DemoBand
    status: str
    concerts: List[DemoConcert]


@dataclass(frozen=True)
class DemoDataset:
    """The full in-memory demo dataset: one band, one tour, its venues and
    concerts."""

    band: DemoBand
    tour: DemoTour
    venues: List[DemoVenue]
    concerts: List[DemoConcert]


def build_demo_dataset(now: Optional[datetime] = None) -> DemoDataset:
    """Build the "band builds and follows a tour" demo scenario in memory.

    `now` anchors which concerts land in the past vs. the future; it
    defaults to the current time so callers get a believable schedule
    without arguments, while tests can inject a fixed value for
    deterministic assertions. Calling this twice with the same `now`
    yields equal data: it reads only `src.demo.config` and never touches a
    database session.
    """
    now = now or datetime.now(timezone.utc)

    venues = [
        DemoVenue(name=name, city=city, country=country, capacity=capacity)
        for name, city, country, capacity in _VENUE_POOL[: config.DEMO_VENUE_COUNT]
    ]

    tier_names = config.DEMO_TICKET_TIER_NAMES
    tier_prices = config.DEMO_TICKET_TIER_PRICES

    concerts = [
        DemoConcert(
            venue=venue,
            date_time=now + timedelta(days=_DAY_OFFSETS[index % len(_DAY_OFFSETS)]),
            ticket_tiers=[
                DemoTicketTier(name=tier_name, price=tier_price)
                for tier_name, tier_price in zip(tier_names, tier_prices)
            ],
        )
        for index, venue in enumerate(venues)
    ]

    band = DemoBand(name=config.DEMO_BAND_NAME)
    tour = DemoTour(
        name=config.DEMO_TOUR_NAME,
        band=band,
        status=TourStatus.ACTIVE.value,
        concerts=concerts,
    )

    return DemoDataset(band=band, tour=tour, venues=venues, concerts=concerts)
