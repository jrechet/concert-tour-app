"""Concert-facing dashboard endpoints, including HTMX concert-card fragments."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Concert

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
