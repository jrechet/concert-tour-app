"""Query logic backing the venue listing endpoint."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Venue


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
