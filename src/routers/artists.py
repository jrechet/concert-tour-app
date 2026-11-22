"""Artist listing and concert endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Artist
from ..schemas.artist import ArtistDetail, ArtistSummary, ArtistUpdate
from ..schemas.concert import ArtistConcertRead
from ..services.artist_service import artist_exists, get_artist_detail, get_by_name, list_artists_with_tour_counts
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


@router.get("/{artist_id}", response_model=ArtistDetail)
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    """Retrieve a single artist by id together with its count of
    non-cancelled concerts. Raises 404 when `artist_id` is unknown."""
    detail = get_artist_detail(db, artist_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return detail


@router.patch("/{artist_id}", response_model=ArtistDetail)
def update_artist(artist_id: int, payload: ArtistUpdate, db: Session = Depends(get_db)):
    """Rename an artist. Raises 404 when `artist_id` is unknown, and 409
    when another artist already holds the requested name (renaming an
    artist to its own current name is a no-op success, not a 409).

    The `get_by_name` pre-check is only a fast path: a concurrent rename
    could still race past it, so a 409 from the `uq_artists_name`
    constraint on commit is handled the same way.
    """
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")

    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] != artist.name:
        if get_by_name(db, updates["name"], exclude_id=artist_id) is not None:
            raise HTTPException(status_code=409, detail="An artist with that name already exists")
        artist.name = updates["name"]
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="An artist with that name already exists")
        db.refresh(artist)

    return get_artist_detail(db, artist_id)


@router.get("/{artist_id}/concerts", response_model=List[ArtistConcertRead])
def get_artist_concerts(artist_id: str, db: Session = Depends(get_db)):
    """Retrieve every non-cancelled concert on whose lineup the artist
    appears, ordered soonest-first. Raises 404 when `artist_id` is
    unknown; an existing artist with no matching concerts returns an
    empty list."""
    if not artist_exists(db, artist_id):
        raise HTTPException(status_code=404, detail="Artist not found")
    return list_concerts_for_artist(db, artist_id)
