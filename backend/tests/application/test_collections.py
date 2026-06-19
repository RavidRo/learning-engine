from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from learning_engine.application.collections import (
    list_collections,
    remove_update_from_collection,
    save_update_to_collection,
)
from learning_engine.domain.collections import (
    CollectionId,
    CollectionNotFoundError,
    Collections,
    SavedCollectionUpdate,
    SavedUpdateSnapshot,
    SaveUpdateToCollection,
    UpdateCollection,
    deterministic_update_key,
)
from learning_engine.domain.updates import SourceInterest

SAVED_AT = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)
EXPECTED_SAVED_UPDATE_COUNT = 3


class StubCollectionRepository:
    def __init__(self) -> None:
        self.saved_updates: dict[tuple[CollectionId, str], SavedCollectionUpdate] = {}
        self.removed: list[tuple[CollectionId, str]] = []

    def ensure_data_store(self) -> None:
        return None

    def list_collections(self) -> Collections:
        return Collections(
            collections=[
                UpdateCollection(id="see-later", name="See Later"),
                UpdateCollection(id="liked", name="Liked"),
                UpdateCollection(id="history", name="History"),
            ]
        )

    def save_update_to_collection(
        self,
        collection_id: CollectionId,
        update_key: str,
        update: SavedUpdateSnapshot,
        saved_at: datetime,
    ) -> SavedCollectionUpdate:
        saved_update = self.saved_updates.get((collection_id, update_key))
        if saved_update is not None:
            return saved_update
        saved_update = SavedCollectionUpdate(update_key=update_key, saved_at=saved_at, update=update)
        self.saved_updates[(collection_id, update_key)] = saved_update
        return saved_update

    def remove_update_from_collection(self, collection_id: CollectionId, update_key: str) -> None:
        self.removed.append((collection_id, update_key))
        self.saved_updates.pop((collection_id, update_key), None)


def test_list_collections_returns_fixed_collections() -> None:
    payload = list_collections(StubCollectionRepository())

    assert [(collection.id, collection.name) for collection in payload.collections] == [
        ("see-later", "See Later"),
        ("liked", "Liked"),
        ("history", "History"),
    ]


def test_saved_update_snapshot_requires_update_url() -> None:
    with pytest.raises(ValidationError, match="Update URL is required"):
        SavedUpdateSnapshot(source_interest=_source_interest(), title="Missing URL", url=" ")


def test_deterministic_update_key_uses_source_identity_and_update_url() -> None:
    update = _update(
        source_id="feed-one",
        source_url="https://example.com/feed.xml",
        url="https://example.com/post",
    )
    same_identity = _update(
        source_id="feed-one",
        source_url="https://changed.example/feed.xml",
        url="https://example.com/post",
    )
    different_source = _update(
        source_id="feed-two",
        source_url="https://example.com/feed.xml",
        url="https://example.com/post",
    )

    assert deterministic_update_key(update) == deterministic_update_key(same_identity)
    assert deterministic_update_key(update) != deterministic_update_key(different_source)


def test_deterministic_update_key_falls_back_to_source_url_when_source_id_is_missing() -> None:
    update = _update(
        source_id=None,
        source_url="https://example.com/feed.xml",
        url="https://example.com/post",
    )
    changed_source_url = _update(
        source_id=None,
        source_url="https://example.com/other.xml",
        url="https://example.com/post",
    )

    assert deterministic_update_key(update) != deterministic_update_key(changed_source_url)


def test_save_update_to_collection_is_idempotent_per_collection() -> None:
    repository = StubCollectionRepository()
    command = SaveUpdateToCollection(update=_update())

    first = save_update_to_collection(repository, "see-later", command, now=SAVED_AT)
    second = save_update_to_collection(
        repository,
        "see-later",
        command,
        now=datetime(2026, 6, 14, 12, 0, tzinfo=UTC),
    )
    liked = save_update_to_collection(repository, "liked", command, now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC))
    history = save_update_to_collection(
        repository,
        "history",
        command,
        now=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )

    assert first == second
    assert first.saved_at == SAVED_AT
    assert liked.update_key == first.update_key
    assert liked.saved_at != first.saved_at
    assert history.update_key == first.update_key
    assert history.saved_at != first.saved_at
    assert len(repository.saved_updates) == EXPECTED_SAVED_UPDATE_COUNT


def test_unknown_collection_id_is_rejected_before_repository_write() -> None:
    repository = StubCollectionRepository()

    with pytest.raises(CollectionNotFoundError, match="Collection not found"):
        save_update_to_collection(
            repository,
            "unknown",
            SaveUpdateToCollection(update=_update()),
            now=SAVED_AT,
        )

    with pytest.raises(CollectionNotFoundError, match="Collection not found"):
        remove_update_from_collection(repository, "unknown", "update-key")

    assert repository.saved_updates == {}
    assert repository.removed == []


def test_remove_update_from_collection_delegates_fixed_collection_id() -> None:
    repository = StubCollectionRepository()

    remove_update_from_collection(repository, "liked", "update-key")

    assert repository.removed == [("liked", "update-key")]


def _source_interest(
    *,
    source_id: str | None = "feed-one",
    source_url: str = "https://example.com/feed.xml",
) -> SourceInterest:
    return SourceInterest(
        interest_id="typescript",
        interest_name="TypeScript",
        source_id=source_id,
        source_label="TypeScript Feed",
        source_url=source_url,
        source_type="feed",
    )


def _update(
    *,
    source_id: str | None = "feed-one",
    source_url: str = "https://example.com/feed.xml",
    url: str = "https://example.com/post",
) -> SavedUpdateSnapshot:
    return SavedUpdateSnapshot(
        title="Update",
        url=url,
        summary="Snapshot",
        image_url="https://example.com/image.png",
        published=SAVED_AT,
        source_interest=_source_interest(source_id=source_id, source_url=source_url),
    )
