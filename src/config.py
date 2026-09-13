"""Application configuration sourced from environment variables.

Business-rule values (thresholds, rates, etc.) live here instead of being
hardcoded inline, so they can be tuned per-environment without a code change.
"""

import os

# Fraction of total tickets remaining below which a concert is considered
# "almost sold out" (e.g. 0.10 == fewer than 10% of tickets remain).
ALMOST_SOLD_OUT_THRESHOLD = float(os.environ.get("ALMOST_SOLD_OUT_THRESHOLD", "0.10"))
