"""Tests for the `TOUR_COPY_NAME_SUFFIX` setting."""

import importlib

from src import config


def test_default_tour_copy_name_suffix():
    assert config.TOUR_COPY_NAME_SUFFIX == " (copy)"


def test_tour_copy_name_suffix_overridable_via_env(monkeypatch):
    monkeypatch.setenv("TOUR_COPY_NAME_SUFFIX", " (duplicate)")
    reloaded = importlib.reload(config)

    assert reloaded.TOUR_COPY_NAME_SUFFIX == " (duplicate)"

    importlib.reload(config)
