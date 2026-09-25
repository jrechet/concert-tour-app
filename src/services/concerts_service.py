"""Query logic backing the concerts CSV export and upcoming-concerts endpoints."""

import csv
import io
from datetime import datetime
from typing import Iterator, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..database import get_reference_time
from ..models import Concert

CSV_HEADER = ["date", "city", "venue", "tour"]


def get_upcoming_concerts(db: Session, reference_time: Optional[datetime] = None) -> List[Concert]:
    """Return concerts scheduled today or later, ordered soonest first.

    A concert is upcoming when its calendar date is today or in the
    future, compared against `reference_time` (defaulting to
    `get_reference_time()`, i.e. the app's current date, when omitted).
    Past concerts are excluded entirely.
    """
    if reference_time is None:
        reference_time = get_reference_time()
    return (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(func.date(Concert.date_time) >= func.date(reference_time))
        .order_by(Concert.date_time)
        .all()
    )


def get_concerts_for_export(db: Session) -> List[dict]:
    """Fetch every concert joined with its venue and tour, ordered by date.

    Returns plain dicts (`date`, `city`, `venue`, `tour`) decoupled from the
    HTTP layer, so this can be unit tested without going through the export
    endpoint. Eager-loads `Concert.venue`/`Concert.tour` via `joinedload` to
    avoid N+1 queries. Returns an empty list when there are no concerts.
    """
    concerts = (
        db.query(Concert)
        .options(joinedload(Concert.venue), joinedload(Concert.tour))
        .order_by(Concert.date_time)
        .all()
    )
    return [
        {
            "date": concert.date_time.date().isoformat(),
            "city": concert.venue.city,
            "venue": concert.venue.name,
            "tour": concert.tour.name,
        }
        for concert in concerts
    ]


def generate_concerts_csv(db: Session) -> Iterator[str]:
    """Yield the concerts CSV export, one row per concert, ordered by date.

    The first yielded chunk is always the header row (`date,city,venue,tour`),
    even when there are no concerts. Values are written through Python's
    `csv` module so commas/quotes in city, venue, or tour names are escaped
    correctly.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(CSV_HEADER)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in get_concerts_for_export(db):
        writer.writerow([row["date"], row["city"], row["venue"], row["tour"]])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
