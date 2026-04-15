"""FastAPI application main module."""

from fastapi import FastAPI

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

# Include routers
app.include_router(tours.router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Concert Tour API"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
