"""Venue listing endpoint."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.venue import VenueOut
from ..services.venue_service import list_venues

router = APIRouter(prefix="/api/v1/venues", tags=["venues"])


@router.get("", response_model=List[VenueOut])
def get_venues(
    min_capacity: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve all venues sorted by name ascending.

    When `min_capacity` is provided, only venues with `capacity >=
    min_capacity` are returned. The `ge=0` constraint rejects negative
    values with a 422 before `list_venues` is ever called, so its
    `ValueError` guard for negative input is unreachable from here.
    """
    return list_venues(db, min_capacity=min_capacity)
