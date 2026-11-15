"""Query/aggregation logic backing the revenue and cancellation stats endpoints."""

from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Concert, Tour
from ..schemas.stats import (
    CANCELLATION_RATE_PRECISION,
    CancellationStatsResponse,
    MonthlyRevenue,
    TourCancellationCount,
)


def get_revenue_by_month(db: Session) -> List[MonthlyRevenue]:
    """Return per-month tickets sold and revenue for non-cancelled concerts,
    in one query, ordered by month ascending.

    Grouping is done via `func.extract('year'/'month', ...)` (rather than
    `strftime`/`to_char`) so the query runs unchanged against both SQLite
    and PostgreSQL. Revenue is `tickets_sold * ticket_price` summed across a
    month's concerts; a concert with no `ticket_price` set contributes 0 to
    revenue (it is not excluded from the sum, so its tickets still count).
    Cancelled concerts are excluded entirely, so a month whose concerts are
    all cancelled is absent from the result rather than appearing with 0s.
    """
    year = func.extract("year", Concert.date_time)
    month = func.extract("month", Concert.date_time)
    revenue_expr = func.sum(Concert.tickets_sold * func.coalesce(Concert.ticket_price, 0))
    rows = (
        db.query(
            year.label("year"),
            month.label("month"),
            func.sum(Concert.tickets_sold).label("tickets_sold"),
            revenue_expr.label("revenue"),
        )
        .filter(Concert.is_cancelled.is_(False))
        .group_by(year, month)
        .order_by(year, month)
        .all()
    )
    return [
        MonthlyRevenue(
            month=f"{int(row_year):04d}-{int(row_month):02d}",
            tickets_sold=int(tickets_sold or 0),
            revenue=float(revenue or 0),
        )
        for row_year, row_month, tickets_sold, revenue in rows
    ]


def get_cancellation_stats(db: Session) -> CancellationStatsResponse:
    """Return overall and per-tour concert cancellation statistics.

    `by_tour` is built with a single `JOIN` + `GROUP BY tour_id` aggregate
    query (not one query per tour), and only includes tours with at least
    one cancelled concert, ordered by `cancelled_concerts` descending then
    `tour_id` ascending for a deterministic response.
    """
    total_concerts = db.query(Concert).count()
    cancelled_concerts = db.query(Concert).filter(Concert.is_cancelled.is_(True)).count()

    cancellation_rate = (
        round(cancelled_concerts / total_concerts * 100, CANCELLATION_RATE_PRECISION)
        if total_concerts
        else 0.0
    )

    rows = (
        db.query(
            Tour.id.label("tour_id"),
            Tour.name.label("tour_name"),
            func.count(Concert.id).label("cancelled_concerts"),
        )
        .join(Concert, Concert.tour_id == Tour.id)
        .filter(Concert.is_cancelled.is_(True))
        .group_by(Tour.id, Tour.name)
        .order_by(func.count(Concert.id).desc(), Tour.id.asc())
        .all()
    )
    by_tour = [
        TourCancellationCount(tour_id=row.tour_id, tour_name=row.tour_name, cancelled_concerts=row.cancelled_concerts)
        for row in rows
    ]

    return CancellationStatsResponse(
        total_concerts=total_concerts,
        cancelled_concerts=cancelled_concerts,
        cancellation_rate=cancellation_rate,
        by_tour=by_tour,
    )
