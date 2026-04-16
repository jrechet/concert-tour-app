"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import engine
from .models import Base
from .routers import venues


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Concert Tour API",
    description="API for managing concert tours, venues, and artists",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS based on environment
environment = os.getenv("ENVIRONMENT", "development")
if environment == "development":
    allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
else:
    allowed_origins = ["https://yourdomain.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(venues.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Concert Tour API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
