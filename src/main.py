"""FastAPI application main module."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from .database import engine, get_db
from .models import Base, Concert
from .routers import concerts, stats, tours

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Concert Tour API",
    description="API for managing concert tours and related data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tours.router)
app.include_router(concerts.router)
app.include_router(concerts.api_router)
app.include_router(stats.router)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Concert Tour API"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard(request: Request):
    """Render the dashboard shell; all data is loaded client-side via HTMX."""
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/concerts/{concert_id}", response_class=HTMLResponse)
def read_concert_detail(concert_id: int, request: Request, db: Session = Depends(get_db)):
    """Render the concert detail page: the headliner plus the supporting-act
    lineup in running order (or an empty-state message when none exist)."""
    concert = (
        db.query(Concert)
        .options(
            joinedload(Concert.tour),
            joinedload(Concert.venue),
            joinedload(Concert.lineup),
        )
        .filter(Concert.id == concert_id)
        .first()
    )
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    return templates.TemplateResponse(request, "concert_detail.html", {"concert": concert})
