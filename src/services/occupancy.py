"""Query logic backing tour-level ticket occupancy."""

from typing import NamedTuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Concert, Tour, Venue


class TourNotFoundError(Exception):
    """Raised by `get_tour_occupancy` when no tour with the given id exists."""


class OccupancyResult(NamedTuple):
    """Ticket occupancy for a tour, aggregated over its non-cancelled concerts."""

    tickets_sold: int
    total_capacity: int
    percentage_sold: float


def get_tour_occupancy(db: Session, tour_id: int) -> OccupancyResult:
    """Compute ticket occupancy for a tour, aggregated over its non-cancelled
    concerts.

    `tickets_sold` and `total_capacity` are summed from `Concert.tickets_sold`
    and the linked `Venue.capacity` across the tour's non-cancelled concerts;
    cancelled concerts are excluded from both sums. `percentage_sold` is
    `tickets_sold / total_capacity * 100`, rounded to 2 decimal places, and is
    `0.0` (rather than raising `ZeroDivisionError`) when `total_capacity` is 0,
    e.g. because the tour has no non-cancelled concerts. Raises
    `TourNotFoundError` when no tour with `tour_id` exists.
    """
    if db.query(Tour.id).filter(Tour.id == tour_id).first() is None:
        raise TourNotFoundError(f"Tour {tour_id} not found")

    tickets_sold, total_capacity = (
        db.query(
            func.coalesce(func.sum(Concert.tickets_sold), 0),
            func.coalesce(func.sum(Venue.capacity), 0),
        )
        .join(Venue, Concert.venue_id == Venue.id)
        .filter(Concert.tour_id == tour_id, Concert.is_cancelled.is_(False))
        .first()
    )
    tickets_sold = int(tickets_sold)
    total_capacity = int(total_capacity)

    percentage_sold = round(tickets_sold / total_capacity * 100, 2) if total_capacity > 0 else 0.0

    return OccupancyResult(
        tickets_sold=tickets_sold,
        total_capacity=total_capacity,
        percentage_sold=percentage_sold,
    )
