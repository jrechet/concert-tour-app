from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from .database import engine
from .models import Base
from .routers import concerts, venues, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Concert Tour API",
    description="API for managing concert tours",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(concerts.router)
app.include_router(venues.router)
app.include_router(dashboard.router)


@app.get("/")
def read_root():
    return {"message": "Concert Tour API is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
