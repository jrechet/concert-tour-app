"""Demo dataset builder.

Single source of truth for the "band builds and follows a tour" demo
scenario, shared by the seed script, the API, and the docs.
"""

from .dataset import (
    DemoBand,
    DemoConcert,
    DemoDataset,
    DemoTicketTier,
    DemoTour,
    DemoVenue,
    build_demo_dataset,
)

__all__ = [
    "DemoBand",
    "DemoConcert",
    "DemoDataset",
    "DemoTicketTier",
    "DemoTour",
    "DemoVenue",
    "build_demo_dataset",
]
