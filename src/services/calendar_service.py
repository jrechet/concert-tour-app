"""Build an iCalendar (.ics) feed of a tour's concerts."""

from datetime import time, timezone

from icalendar import Calendar, Event

# No app-wide timezone setting exists yet (see `src/config.py`); default to
# UTC here rather than inline so a future config value can replace it.
DEFAULT_TIMEZONE = timezone.utc

PRODID = "-//concert-tour-app//Tour Calendar//EN"


def build_tour_calendar(tour) -> bytes:
    """Serialize `tour`'s concerts into an iCalendar feed.

    Each concert becomes one VEVENT with a stable UID derived from the
    concert's id, so re-fetching the feed updates existing calendar entries
    instead of duplicating them.
    """
    calendar = Calendar()
    calendar.add("prodid", PRODID)
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")

    for concert in tour.concerts:
        calendar.add_component(_build_event(tour, concert))

    return calendar.to_ical()


def _build_event(tour, concert) -> Event:
    event = Event()
    event.add("uid", f"concert-{concert.id}@concert-tour-app")
    event.add("summary", f"{tour.name} - {concert.venue.city}")
    event.add("location", f"{concert.venue.name}, {concert.venue.city}, {concert.venue.country}")
    event.add("dtstart", _event_start(concert.date_time))
    return event


def _event_start(date_time):
    """The DTSTART value for `date_time`.

    A midnight time component means no specific show time is stored, so the
    event is treated as all-day (a bare `date`); otherwise the full
    date/time is used, localized to `DEFAULT_TIMEZONE`.
    """
    if date_time.time() == time.min:
        return date_time.date()
    return date_time.replace(tzinfo=date_time.tzinfo or DEFAULT_TIMEZONE)
