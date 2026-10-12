"""Idempotent persistence for the demo dataset built by `src.demo.dataset`.

`seed_demo` and `clear_demo` only `add`/`delete`/`flush` within the caller's
session — they never call `commit()` or `rollback()` themselves, so the
caller (the CLI script, a test, or anything else) decides the transaction
boundary. That is what lets `scripts/seed_demo.py --dry-run` run the exact
same insert logic and then roll everything back instead of persisting it.

Every demo row is matched by a natural key (the band's name, a venue's
`(name, city)`, the tour's name, a concert's `(tour_id, venue_id)`, a tier's
`(concert_id, name)`) rather than a separate marker column. Re-running
`seed_demo` without `reset` therefore updates those rows in place instead of
duplicating them, and `clear_demo` can find exactly the rows `seed_demo`
would create again — without touching a same-named row that a real user
happens to have created independently.
"""

from __future__ import annotations

from src.demo.dataset import DemoConcert, DemoTour, DemoVenue, build_demo_dataset
from src.models import Band, Concert, TicketTier, Tour, Venue


def _get_or_create_band(session, name: str) -> Band:
    band = session.query(Band).filter_by(name=name).one_or_none()
    if band is None:
        band = Band(name=name)
        session.add(band)
        session.flush()
    return band


def _get_or_create_venue(session, demo_venue: DemoVenue) -> Venue:
    venue = session.query(Venue).filter_by(name=demo_venue.name, city=demo_venue.city).one_or_none()
    if venue is None:
        venue = Venue(
            name=demo_venue.name,
            city=demo_venue.city,
            country=demo_venue.country,
            capacity=demo_venue.capacity,
        )
        session.add(venue)
        session.flush()
    return venue


def _get_or_create_tour(session, demo_tour: DemoTour, band: Band, concerts: list[DemoConcert]) -> Tour:
    start_date = min(concert.date_time for concert in concerts).date()
    end_date = max(concert.date_time for concert in concerts).date()
    tour = session.query(Tour).filter_by(name=demo_tour.name).one_or_none()
    if tour is None:
        tour = Tour(
            name=demo_tour.name,
            artist=band.name,
            status=demo_tour.status,
            start_date=start_date,
            end_date=end_date,
        )
        session.add(tour)
        session.flush()
    else:
        tour.artist = band.name
        tour.status = demo_tour.status
        tour.start_date = start_date
        tour.end_date = end_date
    return tour


def _get_or_create_concert(session, tour: Tour, venue: Venue, demo_concert: DemoConcert) -> Concert:
    base_price = demo_concert.ticket_tiers[0].price if demo_concert.ticket_tiers else None
    concert = session.query(Concert).filter_by(tour_id=tour.id, venue_id=venue.id).one_or_none()
    if concert is None:
        concert = Concert(
            tour_id=tour.id,
            venue_id=venue.id,
            date_time=demo_concert.date_time,
            ticket_price=base_price,
        )
        session.add(concert)
        session.flush()
    else:
        concert.date_time = demo_concert.date_time
        concert.ticket_price = base_price
    return concert


def _sync_ticket_tiers(session, concert: Concert, demo_concert: DemoConcert) -> None:
    existing_tiers = {tier.name: tier for tier in session.query(TicketTier).filter_by(concert_id=concert.id)}
    for demo_tier in demo_concert.ticket_tiers:
        tier = existing_tiers.get(demo_tier.name)
        if tier is None:
            session.add(TicketTier(concert_id=concert.id, name=demo_tier.name, price=demo_tier.price))
        else:
            tier.price = demo_tier.price


def seed_demo(session, *, reset: bool = False) -> None:
    """Persist `build_demo_dataset()`: band, venues, tour, concerts, and
    each concert's ticket tiers, in that dependency order, resolving every
    foreign key from the row just inserted (or found) for its parent.

    Safe to call repeatedly without `reset`: every row is matched by its
    natural key, so re-seeding updates the existing rows instead of
    duplicating them. Pass `reset=True` to wipe any previous demo rows
    first and insert a clean copy.
    """
    if reset:
        clear_demo(session)

    dataset = build_demo_dataset()

    band = _get_or_create_band(session, dataset.band.name)

    venues_by_key = {
        (demo_venue.name, demo_venue.city): _get_or_create_venue(session, demo_venue)
        for demo_venue in dataset.venues
    }

    tour = _get_or_create_tour(session, dataset.tour, band, dataset.concerts)

    for demo_concert in dataset.concerts:
        venue = venues_by_key[(demo_concert.venue.name, demo_concert.venue.city)]
        concert = _get_or_create_concert(session, tour, venue, demo_concert)
        _sync_ticket_tiers(session, concert, demo_concert)

    session.flush()


def clear_demo(session) -> None:
    """Remove exactly the rows `seed_demo` would (re)create: the demo
    tour's ticket tiers, concerts, and the tour itself, then the demo
    venues and band — leaving any other row untouched, including a venue
    that happens to share a demo venue's `(name, city)` but still hosts a
    non-demo concert.
    """
    dataset = build_demo_dataset()

    tour = session.query(Tour).filter_by(name=dataset.tour.name).one_or_none()
    if tour is not None:
        concert_ids = [row.id for row in session.query(Concert.id).filter_by(tour_id=tour.id)]
        if concert_ids:
            session.query(TicketTier).filter(TicketTier.concert_id.in_(concert_ids)).delete(
                synchronize_session=False
            )
            session.query(Concert).filter(Concert.id.in_(concert_ids)).delete(synchronize_session=False)
        session.delete(tour)
        session.flush()

    for demo_venue in dataset.venues:
        venue = session.query(Venue).filter_by(name=demo_venue.name, city=demo_venue.city).one_or_none()
        if venue is None:
            continue
        still_in_use = session.query(Concert).filter_by(venue_id=venue.id).count()
        if not still_in_use:
            session.delete(venue)

    band = session.query(Band).filter_by(name=dataset.band.name).one_or_none()
    if band is not None:
        session.delete(band)

    session.flush()
