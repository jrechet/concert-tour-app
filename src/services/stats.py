"""Query logic backing the monthly revenue stats endpoint."""

from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Concert
from ..schemas.stats import MonthlyRevenue


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
