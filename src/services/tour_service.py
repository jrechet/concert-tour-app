"""Query logic backing tour-level aggregates, such as ticket revenue."""

from decimal import Decimal
from typing import NamedTuple, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Concert, Tour


class TourRevenue(NamedTuple):
    """Ticket revenue for a tour, and the count of concerts it was summed over."""

    revenue: Decimal
    concert_count: int


def get_tour_revenue(db: Session, tour_id: int) -> Optional[TourRevenue]:
    """Compute total ticket revenue for a tour, and the number of concerts
    it was summed over.

    Revenue is `sum(ticket_price * tickets_sold)` across the tour's
    non-cancelled concerts; cancelled concerts are excluded from both the
    revenue and the concert count. Returns `None` when no tour with
    `tour_id` exists, so the router can translate that into a 404.
    """
    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        return None

    revenue_total, concert_count = (
        db.query(
            func.coalesce(func.sum(Concert.ticket_price * Concert.tickets_sold), 0),
            func.count(Concert.id),
        )
        .filter(Concert.tour_id == tour_id, Concert.is_cancelled.is_(False))
        .first()
    )
    return TourRevenue(revenue=Decimal(revenue_total), concert_count=concert_count)
