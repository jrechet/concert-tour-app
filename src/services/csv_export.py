"""Pure CSV serializer for concert rows.

Decoupled from the database and from any web framework so it can be unit
tested in isolation: callers are responsible for fetching concerts (with
their `venue`/`tour` relationships loaded) and pass the resulting objects
in directly.
"""

import csv
import io
from typing import Iterable

CSV_HEADER = ["date", "city", "venue", "tour"]


def concerts_to_csv(concerts: Iterable) -> str:
    """Render `concerts` as CSV text with columns `date,city,venue,tour`.

    Always starts with the header row, even when `concerts` is empty. A
    missing `venue`/`tour` relationship (or a `None` value on it) renders
    as an empty field rather than the literal "None". Quoting/escaping is
    left to the `csv` module, including its `\\r\\n` line terminator.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)

    for concert in concerts:
        venue = concert.venue
        tour = concert.tour
        writer.writerow(
            [
                concert.date_time.date().isoformat(),
                venue.city if venue is not None else "",
                venue.name if venue is not None else "",
                tour.name if tour is not None else "",
            ]
        )

    return buffer.getvalue()
