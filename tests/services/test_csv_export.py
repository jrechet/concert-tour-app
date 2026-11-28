"""Unit tests for `concerts_to_csv`, independent of the database."""

import csv
import io
from datetime import datetime
from types import SimpleNamespace

from src.services.csv_export import CSV_HEADER, concerts_to_csv


def _concert(date_time, venue=None, tour=None):
    return SimpleNamespace(date_time=date_time, venue=venue, tour=tour)


def _venue(name, city):
    return SimpleNamespace(name=name, city=city)


def _tour(name):
    return SimpleNamespace(name=name)


class TestConcertsToCsv:
    """Coverage for `concerts_to_csv`."""

    def test_empty_input_yields_header_row_only(self):
        result = concerts_to_csv([])

        assert result == "date,city,venue,tour\r\n"

    def test_one_concert_yields_header_and_one_row(self):
        concert = _concert(
            datetime(2024, 6, 15, 20, 0, 0),
            venue=_venue("Madison Square Garden", "New York"),
            tour=_tour("Neon Skyline World Tour"),
        )

        result = concerts_to_csv([concert])
        rows = list(csv.reader(io.StringIO(result)))

        assert rows[0] == CSV_HEADER
        assert rows[1] == ["2024-06-15", "New York", "Madison Square Garden", "Neon Skyline World Tour"]
        assert len(rows) == 2

    def test_venue_name_with_comma_and_quote_round_trips(self):
        concert = _concert(
            datetime(2024, 6, 15, 20, 0, 0),
            venue=_venue('The "Garden", Arena', "Washington, D.C."),
            tour=_tour("Test Tour"),
        )

        result = concerts_to_csv([concert])

        assert '"The ""Garden"", Arena"' in result
        assert '"Washington, D.C."' in result

        rows = list(csv.reader(io.StringIO(result)))
        assert rows[1][1] == "Washington, D.C."
        assert rows[1][2] == 'The "Garden", Arena'

    def test_none_tour_yields_trailing_empty_field(self):
        concert = _concert(
            datetime(2024, 6, 15, 20, 0, 0),
            venue=_venue("Madison Square Garden", "New York"),
            tour=None,
        )

        result = concerts_to_csv([concert])
        rows = list(csv.reader(io.StringIO(result)))

        assert rows[1] == ["2024-06-15", "New York", "Madison Square Garden", ""]

    def test_date_is_rendered_as_iso_8601(self):
        concert = _concert(
            datetime(2024, 1, 2, 9, 30, 0),
            venue=_venue("Venue", "City"),
            tour=_tour("Tour"),
        )

        result = concerts_to_csv([concert])
        rows = list(csv.reader(io.StringIO(result)))

        assert rows[1][0] == "2024-01-02"
