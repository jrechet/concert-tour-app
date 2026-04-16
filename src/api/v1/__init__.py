"""API v1 module."""

from fastapi import APIRouter
from .dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(dashboard_router)

__all__ = ["api_router"]
