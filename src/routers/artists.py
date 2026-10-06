"""Artist listing endpoint."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.artist import ArtistSummary
from ..services.artist_service import list_artists_with_tour_counts

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
