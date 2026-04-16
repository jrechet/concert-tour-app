"""Concert Tour Management Application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.database import engine, Base
from src.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield


# Initialize FastAPI app
app = FastAPI(
    title="Concert Tour Management",
    description="API for managing concert tours, venues, and bookings",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = ["http://localhost:3000"]  # Add your frontend URL
if os.getenv("ENVIRONMENT") == "development":
    origins.append("http://localhost:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(api_router)

# Basic health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
