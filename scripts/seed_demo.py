"""Idempotent demo seeding entrypoint (`demo.seed` in theswarm.yaml, and for
any reviewer who wants a working "band with a full tour" locally).

    python scripts/seed_demo.py              # seed once; safe to re-run
    python scripts/seed_demo.py --reset      # wipe any previous demo rows, then reseed
    python scripts/seed_demo.py --dry-run    # run the seeding logic, then roll it back

The database written to is `DATABASE_URL` (via `src.database`, the same
settings/env helper the app itself uses) — never a connection string
hardcoded here.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import Base, SessionLocal, engine  # noqa: E402
from src.demo.seeder import seed_demo  # noqa: E402


def parse_args(argv=None) -> argparse.Namespace:
    """Parse the script's CLI flags."""
    parser = argparse.ArgumentParser(description="Seed (or reset) the demo dataset.")
    parser.add_argument(
        "--reset", action="store_true", help="Wipe any previously seeded demo rows before reseeding."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run the seeding logic, then roll it back without persisting."
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Seed the demo dataset into `DATABASE_URL`; return the process exit code."""
    args = parse_args(argv)
    session = None
    try:
        Base.metadata.create_all(bind=engine)
        session = SessionLocal()
        seed_demo(session, reset=args.reset)
        if args.dry_run:
            session.rollback()
            print("dry run: seeding logic ran, nothing was persisted")
        else:
            session.commit()
            print("demo data seeded")
        return 0
    except Exception as exc:  # noqa: BLE001 - any failure here should exit non-zero, not crash with a traceback
        if session is not None:
            session.rollback()
        print(f"demo seeding failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if session is not None:
            session.close()


if __name__ == "__main__":
    sys.exit(main())
