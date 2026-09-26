import importlib

from src import config


def test_default_pagination_constants():
    assert config.DEFAULT_PAGE_SIZE == 20
    assert config.MAX_PAGE_SIZE == 100


def test_pagination_constants_overridable_via_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_PAGE_SIZE", "5")
    monkeypatch.setenv("MAX_PAGE_SIZE", "50")
    reloaded = importlib.reload(config)

    assert reloaded.DEFAULT_PAGE_SIZE == 5
    assert reloaded.MAX_PAGE_SIZE == 50

    importlib.reload(config)
