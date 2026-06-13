"""Application-layer ports for external behavior."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from learning_engine.domain.collections import (
    CollectionId,
    Collections,
    SavedCollectionUpdate,
    SavedUpdateSnapshot,
)
from learning_engine.domain.interests import Interests, InterestSource
from learning_engine.domain.source_types import SourceType
from learning_engine.domain.updates import SourceUpdate


class InterestRepository(Protocol):
    def ensure_data_store(self) -> None: ...

    def read_interests(self) -> Interests: ...

    def write_interests(self, interests: Interests) -> None: ...


class CollectionRepository(Protocol):
    def ensure_data_store(self) -> None: ...

    def list_collections(self) -> Collections: ...

    def save_update_to_collection(
        self,
        collection_id: CollectionId,
        update_key: str,
        update: SavedUpdateSnapshot,
        saved_at: datetime,
    ) -> SavedCollectionUpdate: ...

    def remove_update_from_collection(self, collection_id: CollectionId, update_key: str) -> None: ...


class SourceUpdateCollector(Protocol):
    async def collect_source_updates(self, source: InterestSource) -> list[SourceUpdate]: ...


class SourceImageProvider(Protocol):
    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
    ) -> str | None: ...
