"""Application configuration sourced from environment variables.

Business-rule values (thresholds, rates, etc.) live here instead of being
hardcoded inline, so they can be tuned per-environment without a code change.
"""

import os

# Fraction of total tickets remaining below which a concert is considered
# "almost sold out" (e.g. 0.10 == fewer than 10% of tickets remain).
ALMOST_SOLD_OUT_THRESHOLD = float(os.environ.get("ALMOST_SOLD_OUT_THRESHOLD", "0.10"))

# Default number of items returned per page when a request does not specify one.
DEFAULT_PAGE_SIZE = int(os.environ.get("DEFAULT_PAGE_SIZE", "20"))

# Upper bound on the number of items a client may request per page.
MAX_PAGE_SIZE = int(os.environ.get("MAX_PAGE_SIZE", "100"))

# Whether the read-only demo endpoints (e.g. GET /api/v1/demo/tour-overview)
# are exposed. Off by default so a production deployment doesn't expose demo
# data unless explicitly opted in.
DEMO_ENABLED = os.environ.get("DEMO_ENABLED", "false").strip().lower() in ("1", "true", "yes")

# Debounce delay, in milliseconds, before the concert list's city search box
# fires its HTMX request after the user stops typing.
CITY_SEARCH_DEBOUNCE_MS = int(os.environ.get("CITY_SEARCH_DEBOUNCE_MS", "300"))
