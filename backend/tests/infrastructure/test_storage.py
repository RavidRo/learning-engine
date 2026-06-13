from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from learning_engine.domain.collections import (
    CollectionId,
    CollectionNotFoundError,
    SavedUpdateSnapshot,
    deterministic_update_key,
)
from learning_engine.domain.interests import Interests
from learning_engine.domain.updates import SourceInterest
from learning_engine.infrastructure.storage import (
    InterestStore,
    StoredCollection,
    StoredInterest,
    StoredInterestSource,
    StoredSavedCollectionUpdate,
    StoredSourceIgnoreKeyword,
    _database_url_for_sqlalchemy,
)


def _sqlite_engine() -> Engine:
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _payload() -> Interests:
    return Interests.model_validate(
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
        assert sorted(keyword.keyword for keyword in stored_keywords) == [
            "beta",
            "nightly",
        ]
    finally:
        engine.dispose()


def test_interest_store_persists_deleted_timestamps_as_datetimes() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        payload = Interests.model_validate(
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


def test_interest_store_starts_empty_instead_of_migrating_json_automatically(
    tmp_path: Path,
) -> None:
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
        store.write_interests(Interests(interests=[]))

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
        payload = Interests.model_validate({"interests": [{"name": "TypeScript"}]})

        with pytest.raises(ValueError, match="Interest id is required"):
            store.write_interests(payload)
    finally:
        engine.dispose()


def test_interest_store_requires_source_ids_for_database_persistence() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        payload = Interests.model_validate(
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
        duplicate_payload = Interests.model_validate(
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
        duplicate_payload = Interests.model_validate(
            {
                "interests": [
                    {
                        "id": "typescript",
                        "name": "TypeScript",
                        "sources": [
                            {
                                "id": "typescript-feed",
                                "type": "feed",
                                "url": "https://example.com/one.xml",
                            },
                            {
                                "id": "typescript-feed",
                                "type": "feed",
                                "url": "https://example.com/two.xml",
                            },
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


def test_interest_store_seeds_fixed_collections_idempotently() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)

        store.ensure_data_store()
        store.ensure_data_store()

        with Session(engine) as session:
            stored_collections = session.exec(select(StoredCollection)).all()

        assert [(collection.collection_id, collection.name) for collection in stored_collections] == [
            ("see-later", "See Later"),
            ("liked", "Liked"),
        ]
    finally:
        engine.dispose()


def test_interest_store_saves_update_snapshots_to_collections() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        update = _saved_update(url="https://example.com/first")
        update_key = deterministic_update_key(update)
        saved_at = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)

        saved = store.save_update_to_collection("see-later", update_key, update, saved_at)

        with Session(engine) as session:
            stored_update = session.exec(select(StoredSavedCollectionUpdate)).one()
        collections = store.list_collections().collections
        see_later = collections[0]
        assert saved.update_key == update_key
        assert stored_update.collection_id == "see-later"
        assert stored_update.url == "https://example.com/first"
        assert stored_update.source_id == "feed"
        assert see_later.saved_updates[0].update.title == "Update"
        assert see_later.saved_updates[0].saved_at == saved_at
        assert collections[1].saved_updates == []
    finally:
        engine.dispose()


def test_interest_store_orders_saved_updates_by_save_time_descending() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        older = _saved_update(url="https://example.com/older")
        newer = _saved_update(url="https://example.com/newer")
        store.save_update_to_collection(
            "liked",
            deterministic_update_key(older),
            older,
            datetime(2026, 6, 13, 12, 0, tzinfo=UTC),
        )
        store.save_update_to_collection(
            "liked",
            deterministic_update_key(newer),
            newer,
            datetime(2026, 6, 14, 12, 0, tzinfo=UTC),
        )

        liked = store.list_collections().collections[1]

        assert [saved.update.url for saved in liked.saved_updates] == [
            "https://example.com/newer",
            "https://example.com/older",
        ]
    finally:
        engine.dispose()


def test_interest_store_repeated_save_preserves_original_timestamp_and_snapshot() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        update = _saved_update(title="Original")
        update_key = deterministic_update_key(update)
        original_saved_at = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)

        first = store.save_update_to_collection("see-later", update_key, update, original_saved_at)
        second = store.save_update_to_collection(
            "see-later",
            update_key,
            update.model_copy(update={"title": "Changed"}),
            datetime(2026, 6, 14, 12, 0, tzinfo=UTC),
        )

        with Session(engine) as session:
            stored_updates = session.exec(select(StoredSavedCollectionUpdate)).all()
        assert first == second
        assert second.saved_at == original_saved_at
        assert second.update.title == "Original"
        assert len(stored_updates) == 1
    finally:
        engine.dispose()


def test_interest_store_saves_same_update_key_to_different_collections() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        update = _saved_update()
        update_key = deterministic_update_key(update)

        store.save_update_to_collection("see-later", update_key, update, datetime(2026, 6, 13, 12, 0, tzinfo=UTC))
        store.save_update_to_collection("liked", update_key, update, datetime(2026, 6, 14, 12, 0, tzinfo=UTC))

        with Session(engine) as session:
            stored_updates = session.exec(select(StoredSavedCollectionUpdate)).all()
        assert sorted(saved.collection_id for saved in stored_updates) == [
            "liked",
            "see-later",
        ]
    finally:
        engine.dispose()


def test_interest_store_removes_saved_update_from_one_collection_only() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        update = _saved_update()
        update_key = deterministic_update_key(update)
        store.save_update_to_collection("see-later", update_key, update, datetime(2026, 6, 13, 12, 0, tzinfo=UTC))
        store.save_update_to_collection("liked", update_key, update, datetime(2026, 6, 14, 12, 0, tzinfo=UTC))

        store.remove_update_from_collection("see-later", update_key)

        collections = store.list_collections().collections
        assert collections[0].saved_updates == []
        assert [saved.update_key for saved in collections[1].saved_updates] == [update_key]
    finally:
        engine.dispose()


def test_interest_store_rejects_unknown_collection_ids() -> None:
    engine = _sqlite_engine()
    try:
        store = InterestStore(engine)
        update = _saved_update()
        update_key = deterministic_update_key(update)
        unknown_collection_id = cast(CollectionId, "unknown")

        with pytest.raises(CollectionNotFoundError, match="Collection not found"):
            store.save_update_to_collection(
                unknown_collection_id,
                update_key,
                update,
                datetime(2026, 6, 13, 12, 0, tzinfo=UTC),
            )

        with pytest.raises(CollectionNotFoundError, match="Collection not found"):
            store.remove_update_from_collection(unknown_collection_id, update_key)
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


def _saved_update(
    *,
    title: str = "Update",
    url: str = "https://example.com/update",
) -> SavedUpdateSnapshot:
    return SavedUpdateSnapshot(
        title=title,
        url=url,
        summary="Saved snapshot",
        image_url="https://example.com/image.png",
        published=datetime(2026, 6, 12, 10, 0, tzinfo=UTC),
        source_interest=SourceInterest(
            interest_id="typescript",
            interest_name="TypeScript",
            source_id="feed",
            source_label="TypeScript Feed",
            source_image_url="https://example.com/source.png",
            source_url="https://example.com/feed.xml",
            source_type="feed",
        ),
    )
