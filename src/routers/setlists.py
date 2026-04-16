from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import Setlist, Song, Concert
from ..schemas import SetlistResponse, SetlistCreate, SetlistReorder

router = APIRouter()


@router.get("/api/v1/concerts/{concert_id}/setlist", response_model=SetlistResponse)
def get_setlist(concert_id: int, db: Session = Depends(get_db)):
    """Get setlist for a concert with total duration"""
    # Verify concert exists
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    
    # Get setlist items with songs
    setlist_query = (
        db.query(Setlist, Song)
        .join(Song, Setlist.song_id == Song.id)
        .filter(Setlist.concert_id == concert_id)
        .order_by(Setlist.order_position)
    )
    
    setlist_items = setlist_query.all()
    
    # Calculate total duration
    total_duration = db.query(func.sum(Song.duration_minutes)).join(
        Setlist, Song.id == Setlist.song_id
    ).filter(Setlist.concert_id == concert_id).scalar() or 0
    
    # Format response
    songs = []
    for setlist_item, song in setlist_items:
        songs.append({
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "duration_minutes": song.duration_minutes,
            "order_position": setlist_item.order_position
        })
    
    return {
        "concert_id": concert_id,
        "songs": songs,
        "total_duration_minutes": total_duration
    }


@router.post("/api/v1/concerts/{concert_id}/setlist/songs")
def add_song_to_setlist(concert_id: int, song_id: int, db: Session = Depends(get_db)):
    """Add a song to a concert's setlist"""
    # Verify concert and song exist
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    # Check if song is already in setlist
    existing = db.query(Setlist).filter(
        Setlist.concert_id == concert_id,
        Setlist.song_id == song_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Song already in setlist")
    
    # Get next order position
    max_position = db.query(func.max(Setlist.order_position)).filter(
        Setlist.concert_id == concert_id
    ).scalar() or 0
    
    # Add to setlist
    setlist_item = Setlist(
        concert_id=concert_id,
        song_id=song_id,
        order_position=max_position + 1
    )
    
    db.add(setlist_item)
    db.commit()
    
    return {"message": "Song added to setlist successfully"}


@router.put("/api/v1/setlists/{setlist_id}/reorder")
def reorder_setlist(setlist_id: int, reorder_data: SetlistReorder, db: Session = Depends(get_db)):
    """Reorder songs in a setlist"""
    # Verify setlist item exists
    setlist_item = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist_item:
        raise HTTPException(status_code=404, detail="Setlist item not found")
    
    concert_id = setlist_item.concert_id
    new_position = reorder_data.new_position
    
    # Get all setlist items for this concert
    setlist_items = db.query(Setlist).filter(
        Setlist.concert_id == concert_id
    ).order_by(Setlist.order_position).all()
    
    # Remove the item being moved
    moving_item = None
    remaining_items = []
    for item in setlist_items:
        if item.id == setlist_id:
            moving_item = item
        else:
            remaining_items.append(item)
    
    if not moving_item:
        raise HTTPException(status_code=404, detail="Setlist item not found")
    
    # Insert at new position
    if new_position <= 0:
        new_position = 1
    elif new_position > len(setlist_items):
        new_position = len(setlist_items)
    
    # Reorder all items
    new_order = []
    for i, item in enumerate(remaining_items):
        if i + 1 == new_position:
            new_order.append(moving_item)
        new_order.append(item)
    
    # If new position is at the end
    if new_position > len(remaining_items):
        new_order.append(moving_item)
    
    # Update positions
    for i, item in enumerate(new_order):
        item.order_position = i + 1
    
    db.commit()
    
    return {"message": "Setlist reordered successfully"}


@router.delete("/api/v1/setlists/{setlist_id}")
def delete_setlist_item(setlist_id: int, db: Session = Depends(get_db)):
    """Remove a song from setlist"""
    setlist_item = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist_item:
        raise HTTPException(status_code=404, detail="Setlist item not found")
    
    concert_id = setlist_item.concert_id
    removed_position = setlist_item.order_position
    
    # Delete the item
    db.delete(setlist_item)
    
    # Update positions of remaining items
    remaining_items = db.query(Setlist).filter(
        Setlist.concert_id == concert_id,
        Setlist.order_position > removed_position
    ).all()
    
    for item in remaining_items:
        item.order_position -= 1
    
    db.commit()
    
    return {"message": "Song removed from setlist successfully"}


@router.post("/api/v1/concerts/{concert_id}/setlist/clone/{source_concert_id}")
def clone_setlist(concert_id: int, source_concert_id: int, db: Session = Depends(get_db)):
    """Clone setlist from source concert to target concert"""
    # Verify both concerts exist
    target_concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not target_concert:
        raise HTTPException(status_code=404, detail="Target concert not found")
    
    source_concert = db.query(Concert).filter(Concert.id == source_concert_id).first()
    if not source_concert:
        raise HTTPException(status_code=404, detail="Source concert not found")
    
    # Check if target concert already has a setlist
    existing_setlist = db.query(Setlist).filter(Setlist.concert_id == concert_id).first()
    if existing_setlist:
        raise HTTPException(status_code=400, detail="Target concert already has a setlist")
    
    # Get source setlist
    source_setlist = db.query(Setlist).filter(
        Setlist.concert_id == source_concert_id
    ).order_by(Setlist.order_position).all()
    
    if not source_setlist:
        raise HTTPException(status_code=404, detail="Source concert has no setlist")
    
    # Clone setlist items
    cloned_items = []
    for item in source_setlist:
        cloned_item = Setlist(
            concert_id=concert_id,
            song_id=item.song_id,
            order_position=item.order_position
        )
        cloned_items.append(cloned_item)
    
    db.add_all(cloned_items)
    db.commit()
    
    return {"message": f"Setlist cloned successfully from concert {source_concert_id}"}
