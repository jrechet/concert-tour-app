"""Query logic for artist-level aggregates derived from tours."""

from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import LineupEntry, Tour


def artist_exists(db: Session, artist_id: str) -> bool:
    """Return whether any artist named `artist_id` is known to the system.

    There is no dedicated `Artist` table in this schema, so `artist_id` is
    the artist's name itself (mirroring `list_artists_with_tour_counts`
    below). An artist is known when they headline at least one tour
    (`Tour.artist`) or appear on at least one concert's lineup
    (`LineupEntry.artist_name`), so callers can distinguish an unknown
    artist from one who simply has no (upcoming) concerts.
    """
    headlines_a_tour = db.query(Tour.id).filter(Tour.artist == artist_id).first() is not None
    is_in_a_lineup = db.query(LineupEntry.id).filter(LineupEntry.artist_name == artist_id).first() is not None
    return headlines_a_tour or is_in_a_lineup


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
