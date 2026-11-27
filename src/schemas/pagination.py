"""Shared pagination contract for list endpoints.

`DEFAULT_PAGE_SIZE`/`MAX_PAGE_SIZE` live in `src.config` (environment-driven),
not hardcoded here, so a single env var change tunes every endpoint built on
`PaginationParams`.
"""

from pydantic import BaseModel, Field, computed_field

from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class PaginationParams(BaseModel):
    """Validated `page`/`page_size` query parameters.

    `page_size` is capped at `MAX_PAGE_SIZE`; an out-of-range `page`,
    `page_size`, or a non-positive value raises a `ValidationError` rather
    than being silently clamped, matching the concerts list endpoint's
    existing pagination contract.
    """

    page: int = Field(1, ge=1, description="1-indexed page number")
    page_size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Items per page, up to {MAX_PAGE_SIZE}",
    )

    @computed_field
    @property
    def offset(self) -> int:
        """Number of items to skip before this page starts."""
        return (self.page - 1) * self.page_size

    @computed_field
    @property
    def limit(self) -> int:
        """Alias for `page_size`, matching the `offset`/`limit` naming used
        by query-building callers."""
        return self.page_size
