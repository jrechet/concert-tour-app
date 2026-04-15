from fastapi import FastAPI
from src.database import create_tables
from src.models import Tour, Concert

app = FastAPI(
    title="Concert Tour API",
    description="API for managing concert tours and events",
    version="1.0.0"
)


@app.on_event("startup")
def startup_event():
    create_tables()


@app.get("/")
def read_root():
    return {"message": "Concert Tour API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
