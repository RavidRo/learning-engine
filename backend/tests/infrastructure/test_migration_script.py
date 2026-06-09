from __future__ import annotations

import json
from pathlib import Path

from learning_engine.domain.interests import InterestsPayload
from learning_engine.infrastructure.storage import create_interest_store
from scripts.migrate_interests_json_to_postgres import migrate_interests_json_to_postgres


def _database_url(path: Path) -> str:
    return f"sqlite:///{path}"


def test_migrate_interests_json_to_postgres_writes_legacy_json_payload(tmp_path: Path) -> None:
    source = tmp_path / "interests.json"
    source.write_text(
        json.dumps(
            {
                "interests": [
                    {
                        "id": "typescript",
                        "name": " TypeScript ",
                        "sources": [{"id": "typescript-feed", "type": "feed", "url": "https://example.com/feed.xml"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    database_url = _database_url(tmp_path / "interests.sqlite")

    exit_code = migrate_interests_json_to_postgres(source, database_url, replace=False)

    store = create_interest_store(database_url)
    try:
        interests = store.read_interests()
        assert exit_code == 0
        assert interests.interests[0].id == "typescript"
        assert interests.interests[0].name == "TypeScript"
    finally:
        store.engine.dispose()


def test_migrate_interests_json_to_postgres_requires_replace_for_existing_data(tmp_path: Path) -> None:
    source = tmp_path / "interests.json"
    source.write_text(
        json.dumps(
            {
                "interests": [
                    {
                        "id": "react",
                        "name": "React",
                        "sources": [{"id": "react-feed", "type": "feed", "url": "https://example.com/feed.xml"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    database_url = _database_url(tmp_path / "interests.sqlite")
    store = create_interest_store(database_url)
    try:
        store_payload = InterestsPayload.model_validate(
            {
                "interests": [
                    {
                        "id": "typescript",
                        "name": "TypeScript",
                        "sources": [{"id": "typescript-feed", "type": "feed", "url": "https://example.com/feed.xml"}],
                    }
                ]
            }
        )
        store.write_interests(store_payload)

        exit_code = migrate_interests_json_to_postgres(source, database_url, replace=False)

        assert exit_code == 1
        assert store.read_interests().model_dump(mode="json", by_alias=True) == store_payload.model_dump(
            mode="json", by_alias=True
        )
    finally:
        store.engine.dispose()
