"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

import httpx
import uvicorn
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query, status

from learning_engine.application.collect_updates import (
    CollectUpdatesDependencies,
    SourceUpdatesCache,
    SourceUpdatesCacheOptions,
    collect_updates,
)
from learning_engine.application.ports import (
    HttpFetcher,
    InterestRepository,
    SourceImageProvider,
    SourceUpdateCollector,
)
from learning_engine.application.resolve_source_image import (
    SourceImageConfigurationError,
    SourceImageProviderError,
    SourceImageProviderUnavailableError,
    resolve_source_image,
)
from learning_engine.common.timeframe import Timeframe
from learning_engine.config import HOST, PORT
from learning_engine.domain.models import InterestsPayload, SourceImageRequest, SourceImageResponse, UpdatesResponse
from learning_engine.infrastructure.fetching import REQUEST_TIMEOUT_SECONDS
from learning_engine.infrastructure.fetching import HttpFetcher as HttpxFetcher
from learning_engine.infrastructure.source_collectors.registry import SourceUpdateCollectorRegistry
from learning_engine.infrastructure.source_images.resolver import SourceImageResolver
from learning_engine.infrastructure.storage import DEFAULT_STORE

SOURCE_UPDATES_CACHE_TTL = timedelta(minutes=5)
SOURCE_UPDATES_CACHE_MAX_ENTRIES = 128
SOURCE_IMAGE_CONFIGURATION_ERROR_STATUS = status.HTTP_400_BAD_REQUEST
SOURCE_IMAGE_PROVIDER_UNAVAILABLE_STATUS = status.HTTP_503_SERVICE_UNAVAILABLE
SOURCE_IMAGE_PROVIDER_ERROR_STATUS = status.HTTP_502_BAD_GATEWAY


def _timeframe_from_days(days: int | None, now: datetime) -> Timeframe:
    if days is None:
        return Timeframe(start=datetime.min.replace(tzinfo=UTC), end=now)
    return Timeframe.ending_at(now, timedelta(days=days))


async def _source_image_response(
    payload: SourceImageRequest,
    http_fetcher: HttpFetcher,
    source_image_provider: SourceImageProvider,
) -> SourceImageResponse:
    try:
        image_url = await resolve_source_image(payload.type, payload.url, http_fetcher, source_image_provider)
    except SourceImageConfigurationError as exc:
        raise HTTPException(status_code=SOURCE_IMAGE_CONFIGURATION_ERROR_STATUS, detail=str(exc)) from exc
    except SourceImageProviderUnavailableError as exc:
        raise HTTPException(status_code=SOURCE_IMAGE_PROVIDER_UNAVAILABLE_STATUS, detail=str(exc)) from exc
    except SourceImageProviderError as exc:
        raise HTTPException(status_code=SOURCE_IMAGE_PROVIDER_ERROR_STATUS, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resolve source image",
        ) from exc
    return SourceImageResponse(image_url=image_url)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_api: FastAPI) -> AsyncIterator[None]:
        repository = cast(InterestRepository, _api.state.interest_repository)
        repository.ensure_data_file()
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            _api.state.http_fetcher = HttpxFetcher(client)
            yield

    api = FastAPI(
        title="Learning Engine",
        summary="Local-first API for personal interests and daily briefing source collection.",
        version="0.3.0",
        lifespan=lifespan,
    )
    api.state.source_updates_cache = TTLCache(
        maxsize=SOURCE_UPDATES_CACHE_MAX_ENTRIES,
        ttl=SOURCE_UPDATES_CACHE_TTL.total_seconds(),
    )
    api.state.interest_repository = DEFAULT_STORE
    api.state.source_update_collector = SourceUpdateCollectorRegistry()
    api.state.source_image_provider = SourceImageResolver()

    @api.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/api/interests", response_model=InterestsPayload)
    def get_interests() -> InterestsPayload:
        repository = cast(InterestRepository, api.state.interest_repository)
        return repository.read_interests()

    @api.post("/api/interests")
    def save_interests(payload: InterestsPayload) -> dict[str, object]:
        repository = cast(InterestRepository, api.state.interest_repository)
        repository.write_interests(payload)
        return {
            "ok": True,
            "saved": repository.read_interests().model_dump(mode="json", by_alias=True),
        }

    @api.post("/api/source-image", response_model=SourceImageResponse)
    async def source_image(payload: SourceImageRequest) -> SourceImageResponse:
        fetcher = cast(HttpFetcher, api.state.http_fetcher)
        source_image_provider = cast(SourceImageProvider, api.state.source_image_provider)
        return await _source_image_response(payload, fetcher, source_image_provider)

    @api.get("/api/updates", response_model=UpdatesResponse)
    async def updates(
        days: Annotated[int | None, Query(ge=1)] = None,
    ) -> UpdatesResponse:
        timeframe = _timeframe_from_days(days, datetime.now(UTC))
        cache_scope = "all" if days is None else f"days:{days}"
        source_updates_cache = cast(SourceUpdatesCache, api.state.source_updates_cache)
        source_updates_cache_options = SourceUpdatesCacheOptions(
            cache=source_updates_cache,
            scope=cache_scope,
        )
        repository = cast(InterestRepository, api.state.interest_repository)
        fetcher = cast(HttpFetcher, api.state.http_fetcher)
        source_update_collector = cast(SourceUpdateCollector, api.state.source_update_collector)
        source_image_provider = cast(SourceImageProvider, api.state.source_image_provider)
        return await collect_updates(
            repository.read_interests(),
            timeframe=timeframe,
            dependencies=CollectUpdatesDependencies(
                http_fetcher=fetcher,
                source_update_collector=source_update_collector,
                source_image_provider=source_image_provider,
            ),
            source_updates_cache=source_updates_cache_options,
        )

    return api


app = create_app()


def run() -> None:
    uvicorn.run("learning_engine.presentation.fastapi_app:app", host=HOST, port=PORT, reload=False)
