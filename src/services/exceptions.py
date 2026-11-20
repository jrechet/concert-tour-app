"""Domain errors shared across service modules.

Kept separate from any single service module so callers (e.g. routers) can
import and catch them without importing the service itself.
"""


class TourNotFound(Exception):
    """Raised when no tour exists with the given id. `tour_id` is the id
    that was looked up."""

    def __init__(self, tour_id: int):
        self.tour_id = tour_id
        super().__init__(f"Tour {tour_id} not found")


class NoUpcomingConcert(Exception):
    """Raised when a tour exists but has no non-cancelled concert left to
    come. `tour_id` is the id of the tour that was looked up."""

    def __init__(self, tour_id: int):
        self.tour_id = tour_id
        super().__init__(f"Tour {tour_id} has no upcoming concert")
