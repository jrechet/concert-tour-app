"""Query logic backing the concerts CSV export endpoint."""

import csv
import io
from typing import Iterator

from sqlalchemy.orm import Session, joinedload

from ..models import Concert

CSV_HEADER = ["date", "city", "venue", "tour"]


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

    concerts = (
        db.query(Concert)
        .options(joinedload(Concert.venue), joinedload(Concert.tour))
        .order_by(Concert.date_time)
        .all()
    )
    for concert in concerts:
        writer.writerow(
            [
                concert.date_time.date().isoformat(),
                concert.venue.city,
                concert.venue.name,
                concert.tour.name,
            ]
        )
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
