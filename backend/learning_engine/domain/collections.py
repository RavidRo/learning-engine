"""Collection domain models."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from learning_engine.domain.updates import SourceInterest, Update

CollectionId = Literal["see-later", "liked", "history"]

SEE_LATER_COLLECTION_ID: CollectionId = "see-later"
LIKED_COLLECTION_ID: CollectionId = "liked"
HISTORY_COLLECTION_ID: CollectionId = "history"
FIXED_COLLECTIONS: dict[CollectionId, str] = {
    SEE_LATER_COLLECTION_ID: "See Later",
    LIKED_COLLECTION_ID: "Liked",
    HISTORY_COLLECTION_ID: "History",
}


class CollectionNotFoundError(Exception):
    """Raised when a command references an unknown fixed collection."""


class SavedUpdateSnapshot(Update):
    """Update snapshot persisted inside a collection."""

    url: str

    @field_validator("url")
    @classmethod
    def require_url(cls, value: str | None) -> str:
        return _required_update_url(value)


class SaveUpdateToCollection(BaseModel):
    """Input for saving a collected update snapshot."""

    update: SavedUpdateSnapshot


class SavedCollectionUpdate(BaseModel):
    """An update saved to a collection with its save metadata."""

    update_key: str
    saved_at: datetime
    update: SavedUpdateSnapshot


class UpdateCollection(BaseModel):
    """A fixed collection and its saved updates."""

    id: CollectionId
    name: str
    saved_updates: list[SavedCollectionUpdate] = Field(default_factory=list)


class Collections(BaseModel):
    collections: list[UpdateCollection] = Field(default_factory=list)


def collection_name(collection_id: CollectionId) -> str:
    return FIXED_COLLECTIONS[collection_id]


def validate_collection_id(collection_id: str) -> CollectionId:
    if collection_id in FIXED_COLLECTIONS:
        return collection_id
    raise CollectionNotFoundError(f"Collection not found: {collection_id}")


def deterministic_update_key(update: SavedUpdateSnapshot) -> str:
    source_identity = _source_identity(update.source_interest)
    update_url = _required_update_url(update.url)
    key_parts = [
        update.source_interest.source_type,
        source_identity,
        update_url,
    ]
    return sha256("\n".join(key_parts).encode("utf-8")).hexdigest()


def _source_identity(source_interest: SourceInterest) -> str:
    if source_interest.source_id is not None:
        return f"id:{source_interest.source_id.strip()}"
    return f"url:{source_interest.source_url.strip()}"


def _required_update_url(update_url: str | None) -> str:
    if update_url is None:
        raise ValueError("Update URL is required to save an update to a collection")
    stripped = update_url.strip()
    if not stripped:
        raise ValueError("Update URL is required to save an update to a collection")
    return stripped
