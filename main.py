from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown (cleanup if needed)
    pass


app = FastAPI(
    title="Concert Tour App",
    description="A FastAPI application for managing concert tours",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Concert Tour App is running"}


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to Concert Tour App"}
