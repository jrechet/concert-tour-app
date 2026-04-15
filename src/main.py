from fastapi import FastAPI
from .routers import tours, concerts
from .database import engine
from .models import Base

app = FastAPI(title="Concert Tour API", version="1.0.0")

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(tours.router)
app.include_router(concerts.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Concert Tour API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
