"""FastAPI application main module."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .database import engine
from .models import Base
from .routers import tours

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

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


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
