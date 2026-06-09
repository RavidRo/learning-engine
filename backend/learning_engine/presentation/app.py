"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import cast

import httpx
import uvicorn
from cachetools import TTLCache
from fastapi import FastAPI

from learning_engine.application.ports import (
    InterestRepository,
    SourceImageProvider,
    SourceUpdateCollector,
)
from learning_engine.config import APPLICATION_VERSION, HOST, PORT
from learning_engine.infrastructure.fetching import REQUEST_TIMEOUT_SECONDS, Fetcher
from learning_engine.infrastructure.fetching import HttpFetcher as HttpxFetcher
from learning_engine.infrastructure.source_collectors.registry import (
    SourceUpdateCollectorRegistry,
)
from learning_engine.infrastructure.source_images.resolver import SourceImageResolver
from learning_engine.infrastructure.storage import DEFAULT_STORE
from learning_engine.presentation.interests_router import interests_router

SOURCE_UPDATES_CACHE_TTL = timedelta(minutes=5)
SOURCE_UPDATES_CACHE_MAX_ENTRIES = 128
SourceUpdateCollectorFactory = Callable[[Fetcher], SourceUpdateCollector]
SourceImageProviderFactory = Callable[[Fetcher], SourceImageProvider]


@asynccontextmanager
async def lifespan(api: FastAPI) -> AsyncIterator[None]:
    repository = cast(InterestRepository, api.state.interest_repository)
    repository.ensure_data_store()
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        http_fetcher = HttpxFetcher(client)
        source_update_collector_factory = cast(
            SourceUpdateCollectorFactory,
            api.state.source_update_collector_factory,
        )
        source_image_provider_factory = cast(SourceImageProviderFactory, api.state.source_image_provider_factory)
        api.state.source_update_collector = source_update_collector_factory(http_fetcher)
        api.state.source_image_provider = source_image_provider_factory(http_fetcher)
        yield


def create_app() -> FastAPI:
    api = FastAPI(
        title="Learning Engine",
        summary="Local-first API for personal interests and daily briefing source collection.",
        version=APPLICATION_VERSION,
        lifespan=lifespan,
    )
    api.state.source_updates_cache = TTLCache(
        maxsize=SOURCE_UPDATES_CACHE_MAX_ENTRIES,
        ttl=SOURCE_UPDATES_CACHE_TTL.total_seconds(),
    )
    api.state.interest_repository = DEFAULT_STORE
    api.state.source_update_collector_factory = SourceUpdateCollectorRegistry
    api.state.source_image_provider_factory = SourceImageResolver

    @api.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(interests_router(api))

    return api


app = create_app()


def run() -> None:
    uvicorn.run(
        "learning_engine.presentation.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )
