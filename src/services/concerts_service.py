"""Query logic backing the concerts CSV export endpoint."""

import csv
import io
from typing import Iterator, List

from sqlalchemy.orm import Session, joinedload

from ..models import Concert

CSV_HEADER = ["date", "city", "venue", "tour"]


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
