"""Network fetching primitives."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine, Mapping
from copy import deepcopy
from typing import Any, Callable, Protocol, cast
from urllib.parse import urlparse

import httpx
from cachetools import TTLCache

from learning_engine.config import USER_AGENT

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})
REQUEST_TIMEOUT_SECONDS = 15.0
FetchCacheKey = tuple[str, str, tuple[tuple[str, str], ...]]
FetchCacheValue = bytes | dict[str, object]
FetchCache = TTLCache[FetchCacheKey, FetchCacheValue]


class Fetcher(Protocol):
    async def fetch_url(self, url: str) -> bytes: ...

    async def fetch_json(self, url: str, headers: Mapping[str, str]) -> dict[str, object]: ...


def _validate_url(url: str) -> None:
    if urlparse(url).scheme in ALLOWED_URL_SCHEMES:
        return

    msg = "Only HTTP and HTTPS URLs can be fetched"
    raise ValueError(msg)


class HttpFetcher:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def _request_url(self, url: str, headers: Mapping[str, str]) -> bytes:
        _validate_url(url)

        request_headers = {"User-Agent": USER_AGENT}
        request_headers.update(headers)

        response = await self._client.get(url, headers=request_headers)
        response.raise_for_status()
        return response.content

    async def fetch_url(self, url: str) -> bytes:
        return await self._request_url(url, headers={})

    async def fetch_json(self, url: str, headers: Mapping[str, str]) -> dict[str, object]:
        _validate_url(url)
        response = await self._client.get(url, headers={"User-Agent": USER_AGENT, **headers})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("Expected a JSON object response")
        return cast(dict[str, object], payload)


def _headers_cache_part(headers: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(name), str(value)) for name, value in headers.items()))


class CachedFetcher:
    def __init__(self, fetcher: Fetcher, cache: FetchCache) -> None:
        self._fetcher = fetcher
        self._cache = cache
        self._pending: dict[FetchCacheKey, asyncio.Task[FetchCacheValue]] = {}

    async def fetch_url(self, url: str) -> bytes:
        cache_key: FetchCacheKey = ("bytes", url, ())
        cached = self._cache.get(cache_key)
        if isinstance(cached, bytes):
            return cached

        response = await self._fetch_with_cache(cache_key, lambda: self._fetcher.fetch_url(url))
        if not isinstance(response, bytes):
            raise TypeError("Expected cached byte response")
        return response

    async def fetch_json(self, url: str, headers: Mapping[str, str]) -> dict[str, object]:
        cache_key: FetchCacheKey = ("json", url, _headers_cache_part(headers))
        cached = self._cache.get(cache_key)
        if isinstance(cached, dict):
            return deepcopy(cached)

        response = await self._fetch_with_cache(cache_key, lambda: self._fetcher.fetch_json(url, headers))
        if not isinstance(response, dict):
            raise TypeError("Expected cached JSON response")
        return deepcopy(response)

    async def _fetch_with_cache(
        self,
        cache_key: FetchCacheKey,
        load: Callable[[], Coroutine[Any, Any, FetchCacheValue]],
    ) -> FetchCacheValue:
        pending = self._pending.get(cache_key)
        if pending is not None:
            return await pending

        task: asyncio.Task[FetchCacheValue] = asyncio.create_task(load())
        self._pending[cache_key] = task
        try:
            response = await task
        finally:
            self._pending.pop(cache_key, None)

        self._cache[cache_key] = deepcopy(response) if isinstance(response, dict) else response
        return response
