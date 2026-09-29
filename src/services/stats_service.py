"""Query logic backing the stats endpoints.

Cities and venue names are derived from `Venue` rows joined to `Concert` on
its `venue_id` foreign key, so only venues that actually host at least one
concert are included (a venue with no concerts is excluded, rather than
listing every venue in the table).
"""

from datetime import datetime
from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Concert, Venue


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
