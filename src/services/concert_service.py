"""Query logic for an artist's concerts, joined through the concert lineup,
plus the concert duplication service."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from ..models import Concert, ConcertStatus, LineupEntry
from .concerts_service import ConcertNotFoundError


class VenueScheduleConflictError(Exception):
    """Raised by `duplicate_concert` when another non-cancelled concert
    already exists at the source's venue for the requested `date_time`."""


class EmptyLineupError(Exception):
    """Raised by `get_headliner` when `concert_id` identifies a real
    concert whose lineup has no acts, distinguishing it from an unknown
    concert (`ConcertNotFoundError`)."""


def get_headliner(db: Session, concert_id: int) -> LineupEntry:
    """Return the headlining act of `concert_id`'s lineup: the entry with
    the greatest `set_order`, not merely the first row the database
    happens to emit.

    Raises `ConcertNotFoundError` when no concert with `concert_id`
    exists. Raises `EmptyLineupError` when the concert exists but its
    lineup is empty. Raises no HTTP-related errors; turning these into
    response codes is the caller's responsibility.
    """
    concert_exists = db.query(Concert.id).filter(Concert.id == concert_id).first()
    if not concert_exists:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")

    headliner = (
        db.query(LineupEntry)
        .filter(LineupEntry.concert_id == concert_id)
        .order_by(LineupEntry.set_order.desc())
        .first()
    )
    if headliner is None:
        raise EmptyLineupError(f"Concert {concert_id} has no lineup entries")

    return headliner


def cancel_concert(db: Session, concert_id: int) -> Optional[Concert]:
    """Cancel `concert_id`, idempotently.

    Returns `None` when no concert with `concert_id` exists, leaving the
    HTTP-error decision to the router. When the concert is `scheduled`,
    flips its `status` to `ConcertStatus.cancelled` and commits. When it
    is already `cancelled`, returns it untouched -- no write, no commit --
    so a repeated call is a true no-op rather than a second database hit.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if concert is None:
        return None

    if concert.status == ConcertStatus.cancelled:
        return concert

    concert.status = ConcertStatus.cancelled
    db.commit()
    db.refresh(concert)
    return concert


def uncancel_concert(db: Session, concert_id: int) -> Concert:
    """Restore a cancelled concert to `ConcertStatus.scheduled`.

    Raises `ConcertNotFoundError` when no concert with `concert_id` exists.
    The transition itself is delegated to `Concert.uncancel()`, so its
    `ConcertNotCancelledError`/`ConcertDateInPastError` (from
    `src.models.exceptions`) propagate unchanged, and neither writes
    anything to the database. On success, commits once and returns the
    refreshed concert.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if concert is None:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")

    concert.uncancel()

    db.commit()
    db.refresh(concert)
    return concert


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


def duplicate_concert(db: Session, concert_id: int, date_time: datetime) -> Concert:
    """Duplicate a concert onto a new `date_time`, carrying over its tour,
    venue, ticket price, and lineup.

    Raises `ConcertNotFoundError` when no concert with `concert_id` exists.
    Raises `VenueScheduleConflictError` when another non-cancelled concert
    already exists at the source's venue for `date_time`; a concert at a
    different venue, or a cancelled concert, at that same `date_time` does
    not conflict. Neither error writes anything to the database.

    On success, persists a new `Concert` carrying the source's `tour_id`,
    `venue_id`, and `ticket_price`, with `tickets_sold` reset to 0, not
    cancelled, and the requested `date_time`. The source's lineup is copied
    as new `LineupEntry` rows (same `artist_name`/`set_order`/`set_time`,
    not re-pointing to the source's own rows), so mutating the duplicate's
    lineup afterward never alters the source's. Commits once and returns
    the persisted duplicate.
    """
    source = db.query(Concert).filter(Concert.id == concert_id).first()
    if source is None:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")

    conflict = (
        db.query(Concert.id)
        .filter(
            Concert.venue_id == source.venue_id,
            Concert.date_time == date_time,
            Concert.is_cancelled.is_(False),
        )
        .first()
    )
    if conflict is not None:
        raise VenueScheduleConflictError(
            f"Venue {source.venue_id} already has a concert scheduled at {date_time}"
        )

    duplicate = Concert(
        tour_id=source.tour_id,
        venue_id=source.venue_id,
        date_time=date_time,
        ticket_price=source.ticket_price,
        tickets_sold=0,
        is_cancelled=False,
        lineup=[
            LineupEntry(artist_name=entry.artist_name, set_order=entry.set_order, set_time=entry.set_time)
            for entry in source.lineup
        ],
    )
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    return duplicate
