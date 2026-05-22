"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import monotonic
from typing import Annotated, cast

import httpx
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from learning_engine.collector import collect_updates
from learning_engine.config import HOST, PORT, PUBLIC_DIR
from learning_engine.fetching import REQUEST_TIMEOUT_SECONDS, HttpFetcher
from learning_engine.models import InterestsPayload, UpdatesResponse
from learning_engine.storage import ensure_data_file, read_interests, write_interests
from learning_engine.timeframe import Timeframe

UPDATES_CACHE_TTL_SECONDS = 5 * 60
UPDATES_CACHE_MAX_ENTRIES = 128


def _timeframe_from_days(days: int | None, now: datetime) -> Timeframe:
    if days is None:
        return Timeframe(start=datetime.min.replace(tzinfo=UTC), end=now)
    return Timeframe.ending_at(now, timedelta(days=days))


@dataclass(slots=True)
class _UpdatesCacheEntry:
    expires_at: float
    response: UpdatesResponse


class UpdatesCache:
    """Small in-process TTL cache for complete update responses, including partial errors."""

    def __init__(
        self,
        ttl_seconds: int = UPDATES_CACHE_TTL_SECONDS,
        max_entries: int = UPDATES_CACHE_MAX_ENTRIES,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._entries: dict[tuple[int | None], _UpdatesCacheEntry] = {}

    def get(self, key: tuple[int | None]) -> UpdatesResponse | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= monotonic():
            self._entries.pop(key, None)
            return None
        return entry.response.model_copy(deep=True)

    def set(self, key: tuple[int | None], response: UpdatesResponse) -> UpdatesResponse:
        now = monotonic()
        self._prune_expired_entries(now)
        cached = response.model_copy(deep=True)
        self._entries[key] = _UpdatesCacheEntry(
            expires_at=now + self._ttl_seconds,
            response=cached,
        )
        self._enforce_max_entries()
        return cached.model_copy(deep=True)

    def clear(self) -> None:
        self._entries.clear()

    def _prune_expired_entries(self, now: float) -> None:
        for key, entry in list(self._entries.items()):
            if entry.expires_at <= now:
                self._entries.pop(key, None)

    def _enforce_max_entries(self) -> None:
        overflow = len(self._entries) - self._max_entries
        if overflow <= 0:
            return

        oldest_keys = sorted(self._entries, key=lambda key: self._entries[key].expires_at)
        for key in oldest_keys[:overflow]:
            self._entries.pop(key, None)


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
    api.state.updates_cache = UpdatesCache()

    @api.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse(url="/index.html")

    @api.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/api/interests", response_model=InterestsPayload)
    def get_interests() -> InterestsPayload:
        return read_interests()

    @api.post("/api/interests")
    def save_interests(payload: InterestsPayload) -> dict[str, object]:
        write_interests(payload)
        updates_cache = cast(UpdatesCache, api.state.updates_cache)
        updates_cache.clear()
        return {
            "ok": True,
            "saved": read_interests().model_dump(mode="json", by_alias=True),
        }

    @api.get("/api/updates", response_model=UpdatesResponse)
    async def updates(days: Annotated[int | None, Query(ge=1)] = None) -> UpdatesResponse:
        cache_key = (days,)
        updates_cache = cast(UpdatesCache, api.state.updates_cache)
        cached_response = updates_cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        timeframe = _timeframe_from_days(days, datetime.now(UTC))
        fetcher = cast(HttpFetcher | None, getattr(api.state, "http_fetcher", None))
        if fetcher is None:
            response = await collect_updates(read_interests(), timeframe=timeframe)
        else:
            response = await collect_updates(
                read_interests(),
                timeframe=timeframe,
                fetch=fetcher.fetch_url,
                fetch_json=fetcher.fetch_json,
            )
        return updates_cache.set(cache_key, response)

    api.mount(
        "/",
        StaticFiles(directory=PUBLIC_DIR, html=True, check_dir=False),
        name="public",
    )
    return api


app = create_app()


def run() -> None:
    uvicorn.run("learning_engine.app:app", host=HOST, port=PORT, reload=False)
