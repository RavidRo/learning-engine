"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

import httpx
import uvicorn
from cachetools import TTLCache
from fastapi import FastAPI, Query

from learning_engine.collector import (
    SourceUpdatesCache,
    SourceUpdatesCacheOptions,
    collect_updates,
)
from learning_engine.config import HOST, PORT
from learning_engine.fetching import REQUEST_TIMEOUT_SECONDS, HttpFetcher
from learning_engine.models import InterestsPayload, UpdatesResponse
from learning_engine.storage import ensure_data_file, read_interests, write_interests
from learning_engine.timeframe import Timeframe

SOURCE_UPDATES_CACHE_TTL = timedelta(minutes=5)
SOURCE_UPDATES_CACHE_MAX_ENTRIES = 128


def _timeframe_from_days(days: int | None, now: datetime) -> Timeframe:
    if days is None:
        return Timeframe(start=datetime.min.replace(tzinfo=UTC), end=now)
    return Timeframe.ending_at(now, timedelta(days=days))


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_api: FastAPI) -> AsyncIterator[None]:
        ensure_data_file()
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            _api.state.http_fetcher = HttpFetcher(client)
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

    @api.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/api/interests", response_model=InterestsPayload)
    def get_interests() -> InterestsPayload:
        return read_interests()

    @api.post("/api/interests")
    def save_interests(payload: InterestsPayload) -> dict[str, object]:
        write_interests(payload)
        return {
            "ok": True,
            "saved": read_interests().model_dump(mode="json", by_alias=True),
        }

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
        fetcher = cast(HttpFetcher | None, getattr(api.state, "http_fetcher", None))
        if fetcher is None:
            response = await collect_updates(
                read_interests(),
                timeframe=timeframe,
                source_updates_cache=source_updates_cache_options,
            )
        else:
            response = await collect_updates(
                read_interests(),
                timeframe=timeframe,
                fetch=fetcher.fetch_url,
                fetch_json=fetcher.fetch_json,
                source_updates_cache=source_updates_cache_options,
            )
        return response

    return api


app = create_app()


def run() -> None:
    uvicorn.run("learning_engine.app:app", host=HOST, port=PORT, reload=False)
