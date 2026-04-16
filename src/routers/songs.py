from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Song
from ..schemas import SongCreate, SongUpdate, SongResponse

router = APIRouter()


@router.get("/api/v1/songs", response_model=List[SongResponse])
def get_songs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all songs with pagination"""
    songs = db.query(Song).offset(skip).limit(limit).all()
    return songs


@router.post("/api/v1/songs", response_model=SongResponse)
def create_song(song: SongCreate, db: Session = Depends(get_db)):
    """Create a new song"""
    db_song = Song(**song.model_dump())
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


@router.put("/api/v1/songs/{song_id}", response_model=SongResponse)
def update_song(song_id: int, song: SongUpdate, db: Session = Depends(get_db)):
    """Update an existing song"""
    db_song = db.query(Song).filter(Song.id == song_id).first()
    if db_song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    
    update_data = song.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_song, field, value)
    
    db.commit()
    db.refresh(db_song)
    return db_song


@router.delete("/api/v1/songs/{song_id}")
def delete_song(song_id: int, db: Session = Depends(get_db)):
    """Delete a song"""
    db_song = db.query(Song).filter(Song.id == song_id).first()
    if db_song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    
    db.delete(db_song)
    db.commit()
    return {"message": "Song deleted successfully"}
