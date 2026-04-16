from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import venues, concerts, songs, setlists
from .database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Concert Tour API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(venues.router, tags=["venues"])
app.include_router(concerts.router, tags=["concerts"])
app.include_router(songs.router, tags=["songs"])
app.include_router(setlists.router, tags=["setlists"])


@app.get("/")
def read_root():
    return {"message": "Concert Tour API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
