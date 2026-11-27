"""Unit tests for `list_paginated`.

Concerts are created through real ORM fixtures (`create_venues`/`create_tour`/
`create_concert`), so every `Concert.venue_id`/`Concert.tour_id` is a real id
from a committed row rather than a hardcoded literal like `venue_id=1`.
"""

from datetime import datetime, timedelta

from src.repositories.concert_repository import list_paginated
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

NOW = datetime(2026, 1, 1, 12, 0, 0)


def _seed_concerts(db_session, count):
    venues = create_venues(db_session, count=min(count, 11) or 1)
    tour = create_tour(
        db_session, "Pagination Tour", "Test Artist",
        (NOW - timedelta(days=30)).date(),
        (NOW + timedelta(days=200)).date(),
        "active",
    )
    return [
        create_concert(
            db_session, tour, venues[i % len(venues)], day_offset=i, ticket_price="50.00", base_time=NOW,
        )
        for i in range(count)
    ]


class TestListPaginated:
    """Coverage for `src.repositories.concert_repository.list_paginated`."""

    def test_full_first_page_returns_requested_count_and_real_total(self, db_session):
        concerts = _seed_concerts(db_session, 25)

        page, total = list_paginated(db_session, offset=0, limit=20)

        assert len(page) == 20
        assert total == 25
        assert [c.id for c in page] == [c.id for c in concerts[:20]]

    def test_partial_last_page_returns_remaining_rows_and_same_total(self, db_session):
        concerts = _seed_concerts(db_session, 25)

        page, total = list_paginated(db_session, offset=20, limit=20)

        assert len(page) == 5
        assert total == 25
        assert [c.id for c in page] == [c.id for c in concerts[20:25]]

    def test_offset_past_end_returns_empty_list_and_real_total(self, db_session):
        _seed_concerts(db_session, 25)

        page, total = list_paginated(db_session, offset=100, limit=20)

        assert page == []
        assert total == 25

    def test_empty_table_returns_empty_list_and_zero_total(self, db_session):
        page, total = list_paginated(db_session, offset=0, limit=20)

        assert page == []
        assert total == 0

    def test_pages_do_not_overlap_or_skip_rows(self, db_session):
        concerts = _seed_concerts(db_session, 25)

        page_one, _ = list_paginated(db_session, offset=0, limit=20)
        page_two, _ = list_paginated(db_session, offset=20, limit=20)

        combined_ids = [c.id for c in page_one] + [c.id for c in page_two]
        assert combined_ids == [c.id for c in concerts]
        assert len(set(combined_ids)) == len(concerts)
