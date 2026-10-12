"""Tests for the `scripts/seed_demo.py` CLI entrypoint.

Run as real subprocesses against a scratch SQLite file (via `DATABASE_URL`)
rather than importing the script in-process, since the script binds its
database engine from the environment at import time.
"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_DEMO_TABLES = ("bands", "venues", "tours", "concerts", "ticket_tiers")


def _run_cli(db_path, *extra_args):
    return subprocess.run(
        [sys.executable, "scripts/seed_demo.py", *extra_args],
        cwd=REPO_ROOT,
        env={**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"},
        capture_output=True,
        text=True,
        timeout=60,
    )


def _total_rows(db_path):
    if not Path(db_path).exists():
        return 0
    connection = sqlite3.connect(db_path)
    try:
        existing = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        return sum(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in _DEMO_TABLES
            if table in existing
        )
    finally:
        connection.close()


def test_cli_exits_zero_on_success(tmp_path):
    db_path = tmp_path / "demo.db"

    result = _run_cli(db_path)

    assert result.returncode == 0, result.stderr
    assert _total_rows(db_path) > 0


def test_cli_dry_run_writes_nothing(tmp_path):
    db_path = tmp_path / "demo.db"

    result = _run_cli(db_path, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert _total_rows(db_path) == 0


def test_cli_exits_nonzero_on_db_failure(tmp_path):
    unwritable_db_path = tmp_path / "no-such-directory" / "demo.db"

    result = _run_cli(unwritable_db_path)

    assert result.returncode != 0
