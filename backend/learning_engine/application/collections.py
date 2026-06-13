"""Application use cases for update collections."""

from __future__ import annotations

from datetime import UTC, datetime

from learning_engine.application.ports import CollectionRepository
from learning_engine.domain.collections import (
    Collections,
    SavedCollectionUpdate,
    SaveUpdateToCollection,
    deterministic_update_key,
    validate_collection_id,
)


def list_collections(repository: CollectionRepository) -> Collections:
    return repository.list_collections()


def save_update_to_collection(
    repository: CollectionRepository,
    collection_id: str,
    command: SaveUpdateToCollection,
    *,
    now: datetime | None = None,
) -> SavedCollectionUpdate:
    fixed_collection_id = validate_collection_id(collection_id)
    saved_at = now or datetime.now(UTC)
    update_key = deterministic_update_key(command.update)
    return repository.save_update_to_collection(
        fixed_collection_id,
        update_key,
        command.update,
        saved_at,
    )


def remove_update_from_collection(repository: CollectionRepository, collection_id: str, update_key: str) -> None:
    fixed_collection_id = validate_collection_id(collection_id)
    repository.remove_update_from_collection(fixed_collection_id, update_key)
