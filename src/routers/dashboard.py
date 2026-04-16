from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Annotated
from ..database import get_db
from ..services.dashboard_service import DashboardService
from ..schemas.dashboard import (
    TourOverviewResponse,
    DashboardStatsResponse,
    PaginatedUpcomingConcertsResponse
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/tour-overview", response_model=TourOverviewResponse)
def get_tour_overview(db: Session = Depends(get_db)):
    """Get tour overview including name, start/end dates, and progress percentage."""
    service = DashboardService(db)
    return service.get_tour_overview()


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics including totals and revenue estimate."""
    service = DashboardService(db)
    return service.get_dashboard_stats()


@router.get("/upcoming-concerts", response_model=PaginatedUpcomingConcertsResponse)
def get_upcoming_concerts(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db)
):
    """Get paginated list of upcoming concerts for calendar view."""
    service = DashboardService(db)
    return service.get_upcoming_concerts(limit=limit, offset=offset)
