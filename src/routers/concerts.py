"""Concert-facing endpoints: the JSON list/detail API and the HTMX
dashboard concert-card fragments."""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Concert, LineupEntry, Tour, Venue
from ..schemas import ConcertResponse, LineupEntryResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
api_router = APIRouter(prefix="/api/v1/concerts", tags=["concerts"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@api_router.get("/", response_model=List[ConcertResponse])
def get_concerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = Query(
        None, description="Filter concerts to a single venue city (case-insensitive exact match)"
    ),
    artist_name: Optional[str] = Query(
        None, description="Filter concerts to tours whose artist name contains this text (case-insensitive)"
    ),
    db: Session = Depends(get_db)
):
    """Retrieve all concerts with pagination, including remaining ticket
    counts and sold-out status derived from each concert's venue.

    When `city` is provided, results are narrowed to concerts whose venue
    is in that city (case-insensitive exact match) before pagination is
    applied. When `artist_name` is provided, results are narrowed to
    concerts whose tour artist name contains that text (case-insensitive
    substring match) before pagination is applied.
    """
    query = db.query(Concert).options(joinedload(Concert.venue)).order_by(Concert.id)

    if city is not None:
        query = query.join(Concert.venue).filter(func.lower(Venue.city) == city.lower())

    if artist_name is not None:
        query = query.join(Concert.tour).filter(func.lower(Tour.artist).contains(artist_name.lower()))

    concerts = query.offset(skip).limit(limit).all()
    return concerts


@api_router.get("/{concert_id}", response_model=ConcertResponse)
def get_concert(concert_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific concert by ID."""
    concert = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(Concert.id == concert_id)
        .first()
    )
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    return concert


@api_router.get("/{concert_id}/lineup", response_model=List[LineupEntryResponse])
def get_concert_lineup(
    concert_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Retrieve the supporting-act lineup for a concert, in running order
    (ascending `set_order`), with pagination.

    Returns 404 when the concert itself doesn't exist, but an empty list
    (not an error) when the concert exists and simply has no lineup entries.
    """
    concert_exists = db.query(Concert.id).filter(Concert.id == concert_id).first()
    if not concert_exists:
        raise HTTPException(status_code=404, detail="Concert not found")

    entries = (
        db.query(LineupEntry)
        .filter(LineupEntry.concert_id == concert_id)
        .order_by(LineupEntry.set_order)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return entries


@router.get("/concerts")
def get_dashboard_concerts(
    request: Request,
    artist_name: Optional[str] = Query(
        None, description="Filter concerts to tours whose artist name contains this text (case-insensitive)"
    ),
    include_cancelled: bool = Query(
        True, description="When false, cancelled concerts are excluded from the results"
    ),
    db: Session = Depends(get_db),
):
    """Render concert cards showing date, venue, and ticket availability.

    When `artist_name` is provided and non-blank, results are narrowed to
    concerts whose tour artist name contains that text (case-insensitive
    substring match). A blank value — e.g. a cleared search box — is
    treated the same as omitting the filter, restoring the full list.

    When `include_cancelled` is false, cancelled concerts are excluded.
    Defaults to true so the list shows everything unless the caller opts
    into hiding cancelled dates.
    """
    query = db.query(Concert).options(joinedload(Concert.venue)).order_by(Concert.date_time)

    if artist_name:
        query = query.join(Concert.tour).filter(func.lower(Tour.artist).contains(artist_name.lower()))

    if not include_cancelled:
        query = query.filter(Concert.is_cancelled.is_(False))

    concerts = query.all()
    return templates.TemplateResponse(
        request, "dashboard_concerts.html", {"concerts": concerts}
    )
