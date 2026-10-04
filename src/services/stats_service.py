"""Query logic backing the stats endpoints.

Cities and venue names are derived from `Venue` rows joined to `Concert` on
its `venue_id` foreign key, so only venues that actually host at least one
concert are included (a venue with no concerts is excluded, rather than
listing every venue in the table).
"""

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_reference_time
from ..models import Concert, Venue
from ..schemas.stats import PriceStatsResponse

_WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]


def get_distinct_cities(db: Session) -> List[str]:
    """Return the distinct, alphabetically sorted cities of venues hosting
    at least one concert."""
    rows = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Venue.city.isnot(None), Venue.city != "")
        .distinct()
        .order_by(Venue.city)
        .all()
    )
    return [row[0] for row in rows]


def get_concert_counts_by_country(db: Session) -> List[Tuple[str, int]]:
    """Return `(country, concert_count)` tuples for non-cancelled concerts,
    grouped by the hosting venue's country and ordered by count descending.

    A country whose concerts are all cancelled (or that hosts no concerts
    at all) is absent from the result, rather than appearing with a count
    of 0.
    """
    rows = (
        db.query(Venue.country, func.count(Concert.id).label("concert_count"))
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Concert.is_cancelled.is_(False))
        .group_by(Venue.country)
        .order_by(func.count(Concert.id).desc())
        .all()
    )
    return [(row[0], row[1]) for row in rows]


def get_concert_count(db: Session) -> int:
    """Return the total number of concerts, regardless of date."""
    return db.query(Concert).count()


def get_upcoming_concert_count(db: Session, reference_time: datetime) -> int:
    """Return the number of concerts scheduled today or later.

    A concert is upcoming when its calendar date (compared against
    `reference_time`) is today or in the future, matching the definition
    used by `GET /api/v1/concerts/upcoming`.
    """
    return (
        db.query(Concert)
        .filter(func.date(Concert.date_time) >= func.date(reference_time))
        .count()
    )


def get_concert_counts_by_month(db: Session) -> List[Tuple[str, int]]:
    """Return `(month, concert_count)` tuples for non-cancelled concerts,
    grouped by calendar month (`YYYY-MM`) and ordered chronologically
    ascending.

    A month with no non-cancelled concerts is absent from the result,
    rather than appearing with a count of 0.
    """
    month = func.strftime("%Y-%m", Concert.date_time)
    rows = (
        db.query(month.label("month"), func.count(Concert.id).label("concert_count"))
        .filter(Concert.is_cancelled.is_(False))
        .group_by(month)
        .order_by(month)
        .all()
    )
    return [(row[0], row[1]) for row in rows]


def get_distinct_venue_names(db: Session) -> List[str]:
    """Return the distinct, alphabetically sorted names of venues hosting
    at least one concert."""
    rows = (
        db.query(Venue.name)
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Venue.name.isnot(None), Venue.name != "")
        .distinct()
        .order_by(Venue.name)
        .all()
    )
    return [row[0] for row in rows]


def get_concerts_per_weekday(db: Session) -> "OrderedDict[str, int]":
    """Return an ordered mapping of weekday name to non-cancelled concert
    count, keyed Monday through Sunday.

    Every weekday is present even when no concert falls on it (counted as
    0), unlike the other `get_concert_counts_by_*` helpers in this module
    which omit empty buckets. The grouping is done in Python (rather than
    a SQL `GROUP BY`) since `date_time.isoweekday()` behaves the same
    regardless of the underlying database dialect.
    """
    counts = OrderedDict((name, 0) for name in _WEEKDAY_NAMES)
    rows = (
        db.query(Concert.date_time)
        .filter(Concert.is_cancelled.is_(False))
        .all()
    )
    for (date_time,) in rows:
        counts[_WEEKDAY_NAMES[date_time.isoweekday() - 1]] += 1
    return counts


def get_price_stats(db: Session) -> PriceStatsResponse:
    """Compute ticket price statistics over upcoming, non-cancelled concerts
    with a known price.

    A concert is upcoming when its calendar date is today or later (matching
    `get_upcoming_concert_count`'s definition, compared against
    `get_reference_time()`). Cancelled concerts and concerts with no
    `ticket_price` set are excluded. All three fields are `None` when there
    are no eligible concerts; this is checked explicitly via the row count
    rather than assumed from `func.min`/`avg`/`max`'s null-on-empty-set
    behavior.
    """
    reference_time = get_reference_time()
    row = (
        db.query(
            func.count(Concert.id),
            func.min(Concert.ticket_price),
            func.avg(Concert.ticket_price),
            func.max(Concert.ticket_price),
        )
        .filter(func.date(Concert.date_time) >= func.date(reference_time))
        .filter(Concert.is_cancelled.is_(False))
        .filter(Concert.ticket_price.isnot(None))
        .one()
    )
    count, lowest, average, highest = row
    if not count:
        return PriceStatsResponse(lowest=None, average=None, highest=None)
    return PriceStatsResponse(
        lowest=float(lowest),
        average=float(average),
        highest=float(highest),
    )


@dataclass
class CityRevenue:
    """Revenue aggregated for a single city.

    There is no dedicated `City` table in this schema -- `Venue.city` is a
    plain string column -- so `city_id` is the city name itself, the only
    stable identifier available to group venues/concerts by.
    """

    city_id: str
    city_name: str
    revenue: float


def get_revenue_by_city(db: Session) -> List[CityRevenue]:
    """Return per-city revenue for non-cancelled concerts, sorted by revenue
    descending (ties broken by city name ascending).

    Revenue is `tickets_sold * ticket_price` summed across a city's
    concerts. A concert with no `ticket_price` set contributes 0 (it is not
    excluded from the sum). Cancelled concerts are excluded entirely, so a
    city whose concerts are all cancelled is absent from the result; a city
    with only non-cancelled concerts that sum to 0 (e.g. zero tickets sold)
    is still included, with `revenue` equal to 0.
    """
    revenue_expr = func.sum(Concert.tickets_sold * func.coalesce(Concert.ticket_price, 0))
    rows = (
        db.query(Venue.city, revenue_expr.label("revenue"))
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Concert.is_cancelled.is_(False))
        .group_by(Venue.city)
        .order_by(revenue_expr.desc(), Venue.city.asc())
        .all()
    )
    return [
        CityRevenue(city_id=city, city_name=city, revenue=float(revenue or 0))
        for city, revenue in rows
    ]
