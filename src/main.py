from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.database import create_tables
from src.api.routes import tours


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown


app = FastAPI(
    title="Concert Tour API",
    description="API for managing concert tours and venues",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origins for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tours.router)


@app.get("/")
async def root():
    return {"message": "Concert Tour API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
