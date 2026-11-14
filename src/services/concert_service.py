"""Query logic for an artist's concerts, joined through the concert lineup."""

from typing import List

from sqlalchemy.orm import Session, joinedload

from ..models import Concert, LineupEntry


def list_concerts_for_artist(db: Session, artist_id: str) -> List[Concert]:
    """Return every non-cancelled concert on whose lineup `artist_id`
    appears, ordered soonest first.

    There is no dedicated `Artist` table in this schema -- `LineupEntry` is
    the existing lineup association, and its `artist_name` column is the
    only stable identifier available -- so `artist_id` is the artist's name
    itself, mirroring `ArtistConcertCount.artist_id` in `stats_service`.

    The venue is eager-loaded via `joinedload` so reading `venue.city` on
    each result does not issue an extra query per concert. `distinct()`
    guards against a concert appearing twice if the same artist name were
    ever recorded in more than one of its lineup entries.

    Does not check whether the artist exists at all; callers needing to
    distinguish an unknown artist from one with no concerts should pair
    this with `artist_exists`.
    """
    return (
        db.query(Concert)
        .join(LineupEntry, LineupEntry.concert_id == Concert.id)
        .options(joinedload(Concert.venue))
        .filter(LineupEntry.artist_name == artist_id, Concert.is_cancelled.is_(False))
        .order_by(Concert.date_time)
        .distinct()
        .all()
    )
