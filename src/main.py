from fastapi import FastAPI
from src.database import Base, engine
from src.routers import venues

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Concert Tour Management API",
    description="API for managing concert tours, venues, and events",
    version="1.0.0"
)

# Register routers
app.include_router(venues.router)

@app.get("/")
def read_root():
    return {"message": "Concert Tour Management API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
