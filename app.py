from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import os
from contextlib import asynccontextmanager

# Import your models and database setup
from models import Base, Concert, Venue, Setlist, Song, SetlistSong
from database import get_db, engine

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard route"""
    # Get upcoming concerts (concerts after today)
    upcoming_concerts = db.query(Concert).filter(Concert.date >= date.today()).order_by(Concert.date).all()
    
    # Get recent concerts (for activity feed)
    recent_concerts = db.query(Concert).order_by(Concert.date.desc()).limit(5).all()
    
    # Get all concerts count
    total_concerts = db.query(Concert).count()
    
    # Get all venues
    venues = db.query(Venue).all()
    
    # Get all setlists
    setlists = db.query(Setlist).all()
    
    # Calculate total songs across all setlists
    total_songs = db.query(Song).count()
    
    # Calculate average setlist duration
    avg_setlist_duration = 0
    if setlists:
        total_duration = sum([s.total_duration() for s in setlists if s.total_duration() > 0])
        avg_setlist_duration = total_duration / len(setlists) if len(setlists) > 0 else 0
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "upcoming_concerts": upcoming_concerts,
        "recent_concerts": recent_concerts,
        "total_concerts": total_concerts,
        "venues": venues,
        "setlists": setlists,
        "total_songs": total_songs,
        "avg_setlist_duration": avg_setlist_duration
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request, db: Session = Depends(get_db)):
    """Dashboard route alias"""
    return await dashboard(request, db)

@app.get("/concerts", response_class=HTMLResponse)
async def concerts(request: Request, db: Session = Depends(get_db)):
    """Concerts list page"""
    concerts = db.query(Concert).order_by(Concert.date.desc()).all()
    return templates.TemplateResponse("concerts.html", {
        "request": request,
        "concerts": concerts
    })

@app.get("/setlists", response_class=HTMLResponse)
async def setlists(request: Request, db: Session = Depends(get_db)):
    """Setlists page"""
    setlists = db.query(Setlist).all()
    return templates.TemplateResponse("setlists.html", {
        "request": request,
        "setlists": setlists
    })

@app.get("/venues", response_class=HTMLResponse)
async def venues(request: Request, db: Session = Depends(get_db)):
    """Venues page"""
    venues = db.query(Venue).all()
    return templates.TemplateResponse("venues.html", {
        "request": request,
        "venues": venues
    })

@app.get("/concerts/add", response_class=HTMLResponse)
async def add_concert(request: Request, db: Session = Depends(get_db)):
    """Add concert form"""
    venues = db.query(Venue).all()
    setlists = db.query(Setlist).all()
    return templates.TemplateResponse("add_concert.html", {
        "request": request,
        "venues": venues,
        "setlists": setlists
    })

@app.get("/setlists/{setlist_id}", response_class=HTMLResponse)
async def view_setlist(request: Request, setlist_id: int = None, db: Session = Depends(get_db)):
    """View setlist details"""
    if setlist_id:
        setlist = db.query(Setlist).filter(Setlist.id == setlist_id).first()
        if not setlist:
            raise HTTPException(status_code=404, detail="Setlist not found")
        return templates.TemplateResponse("view_setlist.html", {
            "request": request,
            "setlist": setlist
        })
    else:
        # Show all setlists if no ID provided
        setlists = db.query(Setlist).all()
        return templates.TemplateResponse("setlists.html", {
            "request": request,
            "setlists": setlists
        })

@app.get("/venues/add", response_class=HTMLResponse)
async def add_venue(request: Request):
    """Add venue form"""
    return templates.TemplateResponse("add_venue.html", {
        "request": request
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
