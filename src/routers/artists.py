"""Artist listing and concert endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.artist import ArtistSummary
from ..schemas.concert import ArtistConcertRead
from ..services.artist_service import artist_exists, list_artists_with_tour_counts
from ..services.concert_service import list_concerts_for_artist

router = APIRouter(prefix="/api/v1/artists", tags=["artists"])


@router.get("", response_model=List[ArtistSummary])
def get_artists(db: Session = Depends(get_db)):
    """Retrieve each distinct artist with their number of tours, sorted
    alphabetically by name.

    Returns 200 with an empty list (not an error) when there is no data.
    """
    return [
        ArtistSummary(name=name, tour_count=tour_count)
        for name, tour_count in list_artists_with_tour_counts(db)
    ]


@router.get("/{artist_id}/concerts", response_model=List[ArtistConcertRead])
def get_artist_concerts(artist_id: str, db: Session = Depends(get_db)):
    """Retrieve every non-cancelled concert on whose lineup the artist
    appears, ordered soonest-first. Raises 404 when `artist_id` is
    unknown; an existing artist with no matching concerts returns an
    empty list."""
    if not artist_exists(db, artist_id):
        raise HTTPException(status_code=404, detail="Artist not found")
    return list_concerts_for_artist(db, artist_id)
