"""Migrate a legacy interests JSON file into the PostgreSQL interest store."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from learning_engine.config import DATABASE_URL, INTERESTS_FILE
from learning_engine.domain.interests import InterestsPayload
from learning_engine.infrastructure.storage import create_interest_store


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=INTERESTS_FILE,
        help="Path to the legacy interests JSON file.",
    )
    parser.add_argument(
        "--database-url",
        default=DATABASE_URL,
        help="SQLAlchemy database URL for the target interest store.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing database interests if the target store is not empty.",
    )
    return parser.parse_args()


def _read_payload(path: Path) -> InterestsPayload:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return InterestsPayload.model_validate(payload)


def migrate_interests_json_to_postgres(source: Path, database_url: str, *, replace: bool) -> int:
    payload = _read_payload(source)
    store = create_interest_store(database_url)
    try:
        existing_payload = store.read_interests()
        if existing_payload.interests and not replace:
            sys.stdout.write("Target interest store already contains data. Re-run with --replace to overwrite it.\n")
            return 1

        store.write_interests(payload)
        sys.stdout.write(f"Migrated {len(payload.interests)} interests from {source}.\n")
        return 0
    finally:
        store.engine.dispose()


def main() -> int:
    args = _parse_args()
    return migrate_interests_json_to_postgres(args.source, args.database_url, replace=args.replace)


if __name__ == "__main__":
    raise SystemExit(main())
