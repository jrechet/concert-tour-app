"""Concert-facing endpoints: the JSON list/detail API and the HTMX
dashboard concert-card fragments."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db, get_reference_time
from ..models import Concert, LineupEntry, Tour, Venue
from ..schemas import CancelConcertRequest, ConcertResponse, LineupEntryResponse
from ..services.concerts_service import generate_concerts_csv

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
api_router = APIRouter(prefix="/api/v1/concerts", tags=["concerts"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@api_router.get("/", response_model=List[ConcertResponse])
def get_concerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = Query(
        None, description="Filter concerts to venues whose city contains this text (case-insensitive)"
    ),
    venue: Optional[str] = Query(
        None, description="Filter concerts to the venue whose name matches this text (case-insensitive)"
    ),
    artist_name: Optional[str] = Query(
        None, description="Filter concerts to tours whose artist name contains this text (case-insensitive)"
    ),
    include_cancelled: bool = Query(
        True, description="When false, cancelled concerts are excluded from the results"
    ),
    upcoming_only: bool = Query(
        False, description="When true, only concerts today or later are returned, soonest first, and past concerts are excluded rather than appended"
    ),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve all concerts with pagination, including remaining ticket
    counts and sold-out status derived from each concert's venue.

    Results are ordered chronologically by default: upcoming concerts
    (today or later, compared by calendar date against `reference_time`)
    come first, soonest first, with past concerts appended afterward,
    oldest first.

    When `city` is provided and non-blank, results are narrowed to concerts
    whose venue city contains that text (case-insensitive substring match)
    before pagination is applied; a blank value is treated the same as
    omitting the filter. When `venue` is provided and non-blank, results are
    narrowed to concerts whose venue name exactly matches that text
    (case-insensitive) before pagination is applied; a blank value is
    treated the same as omitting the filter, and a name with no matching
    venue yields an empty list rather than an error. When `artist_name` is provided, results are narrowed to
    concerts whose tour artist name contains that text (case-insensitive
    substring match) before pagination is applied. When `include_cancelled`
    is false, cancelled concerts are excluded before pagination is applied;
    it defaults to true so existing clients see no change in behavior. When
    `upcoming_only` is true, past concerts are excluded entirely (rather than
    appended after upcoming ones), so the soonest concert is always first;
    it defaults to false so existing clients see no change in behavior.
    """
    is_past = case(
        (func.date(Concert.date_time) < func.date(reference_time), 1),
        else_=0,
    )
    query = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .order_by(is_past, Concert.date_time)
    )

    if city or venue:
        query = query.join(Concert.venue)
        if city:
            query = query.filter(func.lower(Venue.city).contains(city.lower(), autoescape=True))
        if venue:
            query = query.filter(func.lower(Venue.name) == venue.lower())

    if artist_name is not None:
        query = query.join(Concert.tour).filter(func.lower(Tour.artist).contains(artist_name.lower()))

    if not include_cancelled:
        query = query.filter(Concert.is_cancelled.is_(False))

    if upcoming_only:
        query = query.filter(func.date(Concert.date_time) >= func.date(reference_time))

    concerts = query.offset(skip).limit(limit).all()
    return concerts


@api_router.get("/cities", response_model=List[str])
def get_concert_cities(db: Session = Depends(get_db)):
    """Retrieve the distinct list of cities hosting at least one concert,
    sorted alphabetically, for populating a city filter control.
    """
    rows = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .distinct()
        .order_by(Venue.city)
        .all()
    )
    return [row[0] for row in rows]


@api_router.get("/upcoming", response_model=List[ConcertResponse])
def get_upcoming_concerts(
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve concerts scheduled today or later, ordered soonest first.

    A concert is upcoming when its calendar date (compared against
    `reference_time`) is today or in the future; past concerts are
    excluded entirely rather than appended, unlike `GET /`.
    """
    concerts = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(func.date(Concert.date_time) >= func.date(reference_time))
        .order_by(Concert.date_time)
        .all()
    )
    return concerts


@api_router.get("/export.csv")
def export_concerts_csv(db: Session = Depends(get_db)):
    """Stream every concert as a CSV file with columns date, city, venue, tour.

    Registered ahead of `/{concert_id}` so the literal `export.csv` path
    segment isn't swallowed as a concert ID.
    """
    return StreamingResponse(
        generate_concerts_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=concerts.csv"},
    )


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


@api_router.post("/{concert_id}/cancel", response_model=ConcertResponse)
def cancel_concert(concert_id: int, payload: CancelConcertRequest, db: Session = Depends(get_db)):
    """Cancel a concert, recording the reason.

    Returns 404 for an unknown concert and 409 if the concert is already
    cancelled.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    if concert.is_cancelled:
        raise HTTPException(status_code=409, detail="Concert is already cancelled")

    concert.is_cancelled = True
    concert.cancellation_reason = payload.reason
    db.commit()
    db.refresh(concert)
    return concert


@api_router.post("/{concert_id}/uncancel", response_model=ConcertResponse)
def uncancel_concert(concert_id: int, db: Session = Depends(get_db)):
    """Restore a cancelled concert, clearing the cancellation reason.

    Returns 404 for an unknown concert and 409 if the concert is not
    currently cancelled.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    if not concert.is_cancelled:
        raise HTTPException(status_code=409, detail="Concert is not cancelled")

    concert.is_cancelled = False
    concert.cancellation_reason = None
    db.commit()
    db.refresh(concert)
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
    upcoming_only: bool = Query(
        False, description="When true, only concerts today or later are returned, soonest first, for the public-facing view"
    ),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Render concert cards showing date, venue, and ticket availability.

    When `artist_name` is provided and non-blank, results are narrowed to
    concerts whose tour artist name contains that text (case-insensitive
    substring match). A blank value — e.g. a cleared search box — is
    treated the same as omitting the filter, restoring the full list.

    When `include_cancelled` is false, cancelled concerts are excluded.
    Defaults to true so the list shows everything unless the caller opts
    into hiding cancelled dates.

    When `upcoming_only` is true, past concerts are excluded and the list is
    ordered soonest first, so the first card is always the next upcoming
    show; the template highlights it accordingly. Defaults to false so
    existing callers see no change in behavior.
    """
    query = db.query(Concert).options(joinedload(Concert.venue)).order_by(Concert.date_time)

    if artist_name:
        query = query.join(Concert.tour).filter(func.lower(Tour.artist).contains(artist_name.lower()))

    if not include_cancelled:
        query = query.filter(Concert.is_cancelled.is_(False))

    if upcoming_only:
        query = query.filter(func.date(Concert.date_time) >= func.date(reference_time))

    concerts = query.all()
    return templates.TemplateResponse(
        request,
        "dashboard_concerts.html",
        {"concerts": concerts, "upcoming_only": upcoming_only, "reference_time": reference_time},
    )
