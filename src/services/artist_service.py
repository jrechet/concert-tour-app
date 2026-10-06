"""Query logic for artist-level aggregates derived from tours."""

from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Tour


def list_artists_with_tour_counts(db: Session) -> List[Tuple[str, int]]:
    """Return each distinct artist with the number of tours they have.

    Results are sorted alphabetically by artist name, case-insensitively.
    Returns an empty list when there are no tours in the database.
    """
    rows = (
        db.query(Tour.artist, func.count(Tour.id))
        .group_by(Tour.artist)
        .order_by(func.lower(Tour.artist))
        .all()
    )
    return [(artist, count) for artist, count in rows]
