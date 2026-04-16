from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from .api import concerts, venues, dashboard
from .database import engine
from . import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Concert Tour App", version="1.0.0")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(concerts.router)
app.include_router(venues.router)
app.include_router(dashboard.router)


@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
