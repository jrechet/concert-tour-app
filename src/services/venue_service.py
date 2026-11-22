"""Query logic backing the venue listing endpoint."""

from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..config import SEARCH_RESULT_LIMIT
from ..models import Concert, Venue
from ..schemas.venue import VenueUpdate


class VenueNotFoundError(Exception):
    """Raised by `delete_venue`/`update_venue` when no venue with the given
    id exists."""


class VenueHasConcertsError(Exception):
    """Raised by `delete_venue` when the venue still hosts at least one
    concert. Carries `concert_count` so the caller can report how many."""

    def __init__(self, message: str, concert_count: int):
        super().__init__(message)
        self.concert_count = concert_count


class VenueConflictError(Exception):
    """Raised by `update_venue` when the resulting (name, city) pair
    already belongs to a different venue."""


def list_venues(db: Session, min_capacity: Optional[int] = None) -> List[Venue]:
    """Return all venues sorted by name ascending.

    When `min_capacity` is provided, only venues with `capacity >=
    min_capacity` are returned. Raises `ValueError` when `min_capacity` is
    negative, so the router can translate that into a 400 without
    duplicating the validation.
    """
    if min_capacity is not None and min_capacity < 0:
        raise ValueError("min_capacity must not be negative")

    query = db.query(Venue)
    if min_capacity is not None:
        query = query.filter(Venue.capacity >= min_capacity)
    return query.order_by(Venue.name).all()


def _escape_like_wildcards(text: str) -> str:
    """Escape `\\`, `%`, and `_` so `text` is matched literally by `ILIKE`
    rather than as LIKE wildcards. Must run before wrapping in `%...%` and
    be paired with `escape="\\"` on the `ilike` call.
    """
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_venues(db: Session, q: str) -> List[Venue]:
    """Return venues whose `name` or `city` contains `q` as a
    case-insensitive substring, ordered by name ascending and capped at
    `SEARCH_RESULT_LIMIT` results.

    `%` and `_` in `q` are escaped so they are matched literally rather than
    as LIKE wildcards. A venue matching on both `name` and `city` is still
    returned only once. Returns `[]` when nothing matches.
    """
    pattern = f"%{_escape_like_wildcards(q)}%"
    return (
        db.query(Venue)
        .filter(
            or_(
                Venue.name.ilike(pattern, escape="\\"),
                Venue.city.ilike(pattern, escape="\\"),
            )
        )
        .order_by(Venue.name)
        .limit(SEARCH_RESULT_LIMIT)
        .all()
    )


def get_venue_or_none(db: Session, venue_id: int) -> Optional[Venue]:
    """Return the venue with id `venue_id`, or `None` when it does not
    exist, so callers can distinguish an unknown venue from one with no
    related data.
    """
    return db.query(Venue).filter(Venue.id == venue_id).first()


def list_venue_concerts(db: Session, venue_id: int) -> List[Concert]:
    """Return every non-cancelled concert for the venue with id
    `venue_id`, ordered soonest first.

    Does not check whether the venue itself exists; callers needing to
    distinguish an unknown venue from one with no concerts should pair
    this with `get_venue_or_none`.
    """
    return (
        db.query(Concert)
        .filter(Concert.venue_id == venue_id, Concert.is_cancelled.is_(False))
        .order_by(Concert.date_time)
        .all()
    )


def delete_venue(db: Session, venue_id: int) -> None:
    """Delete the venue with id `venue_id`.

    Raises `VenueNotFoundError` when no venue with `venue_id` exists.
    Raises `VenueHasConcertsError` (carrying the concert count, including
    cancelled ones) when the venue hosts at least one concert, counted via
    `func.count` over `Concert.venue_id` rather than loading every row. In
    both cases no row is touched. On success, deletes the venue and commits.
    """
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if venue is None:
        raise VenueNotFoundError(f"Venue {venue_id} not found")

    concert_count = (
        db.query(func.count(Concert.id)).filter(Concert.venue_id == venue_id).scalar()
    )
    if concert_count > 0:
        raise VenueHasConcertsError(
            f"Venue {venue_id} has {concert_count} concert(s)", concert_count
        )

    db.delete(venue)
    db.commit()


def update_venue(db: Session, venue_id: int, payload: VenueUpdate) -> Venue:
    """Apply a partial update to the venue with id `venue_id`.

    Only the fields actually set on `payload` (via `exclude_unset`) are
    changed; omitted fields keep their stored values. Raises
    `VenueNotFoundError` when no venue with `venue_id` exists. Raises
    `VenueConflictError` when the resulting (name, city) pair already
    belongs to a *different* venue, including when only one of `name`/
    `city` is sent and the venue's own unchanged value on the other field
    completes the duplicate pair. The conflict check excludes the venue
    being updated, so renaming it to its own current name/city is not a
    conflict. On success, commits and returns the refreshed venue.
    """
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if venue is None:
        raise VenueNotFoundError(f"Venue {venue_id} not found")

    updates = payload.model_dump(exclude_unset=True)
    new_name = updates.get("name", venue.name)
    new_city = updates.get("city", venue.city)

    conflict = (
        db.query(Venue.id)
        .filter(Venue.name == new_name, Venue.city == new_city, Venue.id != venue_id)
        .first()
    )
    if conflict is not None:
        raise VenueConflictError(
            f"A venue named '{new_name}' already exists in {new_city}"
        )

    for field, value in updates.items():
        setattr(venue, field, value)

    db.commit()
    db.refresh(venue)
    return venue
