"""Concert-facing endpoints: the JSON list/detail API and the HTMX
dashboard concert-card fragments."""

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Concert
from ..schemas import ConcertResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
api_router = APIRouter(prefix="/api/v1/concerts", tags=["concerts"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@api_router.get("/", response_model=List[ConcertResponse])
def get_concerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Retrieve all concerts with pagination, including remaining ticket
    counts and sold-out status derived from each concert's venue."""
    concerts = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .order_by(Concert.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
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


@router.get("/concerts")
def get_dashboard_concerts(request: Request, db: Session = Depends(get_db)):
    """Render concert cards showing date, venue, and ticket availability."""
    concerts = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .order_by(Concert.date_time)
        .all()
    )
    return templates.TemplateResponse(
        request, "dashboard_concerts.html", {"concerts": concerts}
    )
