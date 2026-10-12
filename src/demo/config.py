"""Tunable values for the demo dataset builder.

The seed script, the API, and the docs all build the same "band builds and
follows a tour" scenario from `src.demo.dataset.build_demo_dataset`. The
values that scenario depends on (band name, venue count, ticket tiers and
their prices) live here instead of being hardcoded inline, so they can be
tuned per-environment without a code change.
"""

import os
from decimal import Decimal

# Name of the band whose tour the demo dataset follows.
DEMO_BAND_NAME = os.environ.get("DEMO_BAND_NAME", "Aurora Belle")

# Name of the tour the demo band is currently following.
DEMO_TOUR_NAME = os.environ.get("DEMO_TOUR_NAME", "Neon Skyline Tour")

# Number of venues (and thus concerts) in the demo tour.
DEMO_VENUE_COUNT = int(os.environ.get("DEMO_VENUE_COUNT", "3"))

# Names of the ticket tiers offered for each demo concert, in order.
DEMO_TICKET_TIER_NAMES = [
    name.strip()
    for name in os.environ.get("DEMO_TICKET_TIER_NAMES", "General Admission,VIP,Premium").split(",")
    if name.strip()
]

# Prices for the ticket tiers above, matched by position.
DEMO_TICKET_TIER_PRICES = [
    Decimal(price.strip())
    for price in os.environ.get("DEMO_TICKET_TIER_PRICES", "75.00,150.00,300.00").split(",")
    if price.strip()
]
