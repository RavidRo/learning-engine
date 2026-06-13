"""Typed access to FastAPI application state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import FastAPI

from learning_engine.application.collect_updates import SourceUpdatesCache
from learning_engine.application.ports import (
    CollectionRepository,
    InterestRepository,
    SourceImageProvider,
    SourceUpdateCollector,
)


@dataclass(frozen=True, slots=True)
class AppState:
    interest_repository: InterestRepository
    collection_repository: CollectionRepository
    source_update_collector: SourceUpdateCollector
    source_image_provider: SourceImageProvider
    source_updates_cache: SourceUpdatesCache


def get_app_state(api: FastAPI) -> AppState:
    return AppState(
        interest_repository=cast(InterestRepository, api.state.interest_repository),
        collection_repository=cast(CollectionRepository, api.state.collection_repository),
        source_update_collector=cast(SourceUpdateCollector, api.state.source_update_collector),
        source_image_provider=cast(SourceImageProvider, api.state.source_image_provider),
        source_updates_cache=cast(SourceUpdatesCache, api.state.source_updates_cache),
    )
