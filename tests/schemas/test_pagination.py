"""Unit tests for the shared `PaginationParams` query-parameter schema,
independent of any specific endpoint."""

import importlib

import pytest
from pydantic import ValidationError

from src import config
from src.schemas import pagination as pagination_module
from src.schemas.pagination import PaginationParams


def test_defaults_use_configured_page_size():
    params = PaginationParams()

    assert params.page == 1
    assert params.page_size == config.DEFAULT_PAGE_SIZE
    assert params.page_size == 20


@pytest.mark.parametrize("page_size", [0, -1])
def test_non_positive_page_size_raises_validation_error(page_size):
    with pytest.raises(ValidationError):
        PaginationParams(page_size=page_size)


@pytest.mark.parametrize("page", [0, -1])
def test_non_positive_page_raises_validation_error(page):
    with pytest.raises(ValidationError):
        PaginationParams(page=page)


def test_page_size_above_max_raises_validation_error():
    with pytest.raises(ValidationError):
        PaginationParams(page_size=config.MAX_PAGE_SIZE + 1)


def test_page_size_at_max_is_valid():
    params = PaginationParams(page_size=config.MAX_PAGE_SIZE)

    assert params.page_size == config.MAX_PAGE_SIZE


@pytest.mark.parametrize(
    "page, page_size, expected_offset",
    [
        (1, 20, 0),
        (2, 20, 20),
        (5, 10, 40),
    ],
)
def test_offset_arithmetic(page, page_size, expected_offset):
    params = PaginationParams(page=page, page_size=page_size)

    assert params.offset == expected_offset
    assert params.offset == page_size * (page - 1)


def test_limit_mirrors_page_size():
    params = PaginationParams(page_size=15)

    assert params.limit == 15
    assert params.limit == params.page_size


def test_defaults_and_max_follow_environment_variables(monkeypatch):
    monkeypatch.setenv("DEFAULT_PAGE_SIZE", "5")
    monkeypatch.setenv("MAX_PAGE_SIZE", "50")
    reloaded_config = importlib.reload(config)
    reloaded_pagination = importlib.reload(pagination_module)

    try:
        params = reloaded_pagination.PaginationParams()
        assert params.page_size == 5

        with pytest.raises(ValidationError):
            reloaded_pagination.PaginationParams(page_size=51)

        reloaded_pagination.PaginationParams(page_size=50)
    finally:
        importlib.reload(config)
        importlib.reload(pagination_module)

    assert reloaded_config.DEFAULT_PAGE_SIZE == 5
    assert reloaded_config.MAX_PAGE_SIZE == 50
