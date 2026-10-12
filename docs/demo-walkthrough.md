# Demo walkthrough

A single entry page (`GET /demo`) that replays the seeded "band builds and
follows a tour" scenario end to end: create a band, add venues, schedule
concerts, track upcoming dates, and see each concert's ticket tiers. It
reads the same aggregated data as `GET /api/v1/demo/tour-overview` — the
page and the JSON API can never show different numbers because they share
one query helper (`src/routers/demo.py`).

The page is **read-only**. The only HTMX interaction on it is an
`hx-get` city filter that swaps the concert list fragment
(`GET /demo/concerts`); there is no `hx-post` or `hx-delete` anywhere on the
page, so no Flask-WTF/CSRF token is needed. Every piece of stored content
(band name, venue name, city) is rendered through Jinja's `|e` escape
filter, so a malicious stored string is shown as inert escaped text,
never executed.

## Environment variables

All of these have defaults and are optional:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEMO_ENABLED` | `false` | Must be `true`/`1`/`yes` to expose `/demo`, `/demo/concerts`, and `/api/v1/demo/tour-overview`. Everything returns `403` when this is off. |
| `DEMO_BAND_NAME` | `Aurora Belle` | Name of the demo band. |
| `DEMO_TOUR_NAME` | `Neon Skyline Tour` | Name of the demo tour. |
| `DEMO_VENUE_COUNT` | `3` | Number of venues/concerts seeded (max 6; see `src/demo/dataset.py`'s venue pool). |
| `DEMO_TICKET_TIER_NAMES` | `General Admission,VIP,Premium` | Comma-separated ticket tier names, applied to every demo concert. |
| `DEMO_TICKET_TIER_PRICES` | `75.00,150.00,300.00` | Comma-separated prices matched by position to the tier names above. |

None of these values are secrets or connection strings — `DATABASE_URL`
(the actual connection string) is configured separately via
`src/database.py` and is never documented here.

## Seeding the demo data

```
DEMO_ENABLED=true python scripts/seed_demo.py --reset
```

`--reset` wipes any previously seeded demo rows (band, venues, tour,
concerts, ticket tiers) before inserting a clean copy. Omit it to reseed
idempotently — rows are matched by natural key (band name, venue
`(name, city)`, tour name, concert `(tour_id, venue_id)`, tier
`(concert_id, name)`), so re-running the script updates existing rows
instead of duplicating them. Add `--dry-run` to exercise the same seeding
logic and then roll it back without persisting anything.

## Replaying the scenario

1. **Call the JSON API**, to see the raw aggregated data:

   ```
   curl "http://localhost:8000/api/v1/demo/tour-overview"
   ```

   Returns the tour's name/artist/status, every concert (venue, city,
   date, status, ticket tiers), and past/upcoming counts. Add
   `?city=<name>` to filter to one city (case-insensitive); a blank city
   is rejected with `422`.

2. **Open the walkthrough page**, to see the same data as a guided story:

   ```
   http://localhost:8000/demo
   ```

   The page renders five steps — create band, add venues, schedule
   concerts, track upcoming dates, ticket tiers — followed by the full
   concert list. Use the city dropdown under "Track upcoming dates" to
   filter the list in place via `hx-get /demo/concerts?city=...`, without
   a full page reload.

Both `/demo` and `/api/v1/demo/tour-overview` respond `403` when
`DEMO_ENABLED` is off, and `404` if the demo dataset hasn't been seeded yet.
