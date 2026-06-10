from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from learning_engine.domain.interests import InterestsPayload
from learning_engine.infrastructure.storage import (
    InterestStore,
    StoredInterest,
    StoredInterestSource,
    StoredSourceIgnoreKeyword,
    _database_url_for_sqlalchemy,
)


def _sqlite_engine() -> Engine:
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _payload() -> InterestsPayload:
    return InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "id": "typescript",
                    "name": " TypeScript ",
                    "sources": [
                        {
                            "id": "typescript-feed",
                            "type": "feed",
                            "url": " https://example.com/feed.xml ",
                            "ignoreKeywords": "nightly, beta",
                            "imageUrl": "https://example.com/image.png",
                        }
                    ],
                }
            ]
        }
    )


def test_interest_store_writes_normalized_interests_to_relational_tables() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        store.write_interests(_payload())

        interests = store.read_interests()

        assert interests.interests[0].id == "typescript"
        assert interests.interests[0].name == "TypeScript"
        assert interests.interests[0].sources[0].id == "typescript-feed"
        assert interests.interests[0].sources[0].url == "https://example.com/feed.xml"
        assert interests.interests[0].sources[0].ignore_keywords == ["beta", "nightly"]
        with Session(engine) as session:
            stored_interest = session.exec(select(StoredInterest)).one()
            stored_source = session.exec(select(StoredInterestSource)).one()
            stored_keywords = session.exec(select(StoredSourceIgnoreKeyword)).all()

        assert stored_interest.interest_id == "typescript"
        assert stored_source.source_id == "typescript-feed"
        assert stored_source.interest_id == "typescript"
        assert stored_source.image_url == "https://example.com/image.png"
        assert sorted(keyword.keyword for keyword in stored_keywords) == ["beta", "nightly"]
    finally:
        engine.dispose()


def test_interest_store_persists_deleted_timestamps_as_datetimes() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        payload = InterestsPayload.model_validate(
            {
                "interests": [
                    {
                        "id": "typescript",
                        "name": "TypeScript",
                        "deletedAt": "2026-05-15T10:00:00.000Z",
                        "sources": [
                            {
                                "id": "typescript-feed",
                                "type": "feed",
                                "url": "https://example.com/feed.xml",
                                "deletedAt": "2026-05-16T11:30:00.000Z",
                            }
                        ],
                    }
                ]
            }
        )

        store.write_interests(payload)

        with Session(engine) as session:
            stored_interest = session.exec(select(StoredInterest)).one()
            stored_source = session.exec(select(StoredInterestSource)).one()

        assert isinstance(stored_interest.deleted_at, datetime)
        assert isinstance(stored_source.deleted_at, datetime)
        assert stored_interest.deleted_at.replace(tzinfo=UTC) == datetime(2026, 5, 15, 10, 0, tzinfo=UTC)
        assert stored_source.deleted_at.replace(tzinfo=UTC) == datetime(2026, 5, 16, 11, 30, tzinfo=UTC)
        saved = store.read_interests().model_dump(mode="json", by_alias=True)
        assert saved["interests"][0]["deletedAt"] == "2026-05-15T10:00:00.000Z"
        assert saved["interests"][0]["sources"][0]["deletedAt"] == "2026-05-16T11:30:00.000Z"
    finally:
        engine.dispose()


def test_interest_store_starts_empty_instead_of_migrating_json_automatically(tmp_path: Path) -> None:
    path = tmp_path / "interests.json"
    path.write_text('{"interests":[{"id":"legacy","name":"Legacy"}]}', encoding="utf-8")
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)

        assert store.read_interests().interests == []
    finally:
        engine.dispose()


def test_interest_store_replaces_removed_interests_and_sources() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        store.write_interests(_payload())
        store.write_interests(InterestsPayload(interests=[]))

        assert store.read_interests().interests == []
        with Session(engine) as session:
            stored_interests = session.exec(select(StoredInterest)).all()
            stored_sources = session.exec(select(StoredInterestSource)).all()
            stored_keywords = session.exec(select(StoredSourceIgnoreKeyword)).all()

        assert stored_interests == []
        assert stored_sources == []
        assert stored_keywords == []
    finally:
        engine.dispose()


def test_interest_store_requires_interest_ids_for_database_persistence() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        payload = InterestsPayload.model_validate({"interests": [{"name": "TypeScript"}]})

        with pytest.raises(ValueError, match="Interest id is required"):
            store.write_interests(payload)
    finally:
        engine.dispose()


def test_interest_store_requires_source_ids_for_database_persistence() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        payload = InterestsPayload.model_validate(
            {
                "interests": [
                    {
                        "id": "typescript",
                        "name": "TypeScript",
                        "sources": [{"type": "feed", "url": "https://example.com/feed.xml"}],
                    }
                ]
            }
        )

        with pytest.raises(ValueError, match="Source id is required"):
            store.write_interests(payload)
    finally:
        engine.dispose()


def test_interest_store_rejects_duplicate_interest_ids_before_replacing_existing_data() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        store.write_interests(_payload())
        duplicate_payload = InterestsPayload.model_validate(
            {
                "interests": [
                    {"id": "typescript", "name": "TypeScript"},
                    {"id": "typescript", "name": "TypeScript Again"},
                ]
            }
        )

        with pytest.raises(ValueError, match="Duplicate interest id"):
            store.write_interests(duplicate_payload)

        assert store.read_interests().interests[0].name == "TypeScript"
    finally:
        engine.dispose()


def test_interest_store_rejects_duplicate_source_ids_before_replacing_existing_data() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        store.write_interests(_payload())
        duplicate_payload = InterestsPayload.model_validate(
            {
                "interests": [
                    {
                        "id": "typescript",
                        "name": "TypeScript",
                        "sources": [
                            {"id": "typescript-feed", "type": "feed", "url": "https://example.com/one.xml"},
                            {"id": "typescript-feed", "type": "feed", "url": "https://example.com/two.xml"},
                        ],
                    }
                ]
            }
        )

        with pytest.raises(ValueError, match="Duplicate source id"):
            store.write_interests(duplicate_payload)

        assert store.read_interests().interests[0].sources[0].url == "https://example.com/feed.xml"
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        (
            "postgres://user:password@example.com:5432/app",
            "postgresql+psycopg://user:password@example.com:5432/app",
        ),
        (
            "postgresql://user:password@example.com:5432/app",
            "postgresql+psycopg://user:password@example.com:5432/app",
        ),
        (
            "postgresql+psycopg://user:password@example.com:5432/app",
            "postgresql+psycopg://user:password@example.com:5432/app",
        ),
    ],
)
def test_database_url_for_sqlalchemy_uses_installed_postgres_driver(database_url: str, expected: str) -> None:
    assert _database_url_for_sqlalchemy(database_url) == expected
