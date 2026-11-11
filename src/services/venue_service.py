"""Query logic backing the venue listing endpoint."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Concert, Venue


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
