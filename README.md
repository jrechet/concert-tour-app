# Concert Tour App

Manage dates, venues, and logistics for touring bands.

Built with FastAPI + HTMX.

## Demo data

`scripts/seed_demo.py` fills an empty database with a small tour schedule
(three tours, six concerts, dates relative to today) and leaves one that
already has tours alone. The swarm's QA runs it on every demo server, each
on a database of its own (`theswarm.yaml` → `demo.seed`, `demo.env`):

    DATABASE_URL=sqlite:///demo.db python scripts/seed_demo.py

