"""Network fetching primitives."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast
from urllib.parse import urlparse

import httpx

from learning_engine.config import USER_AGENT

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})
REQUEST_TIMEOUT_SECONDS = 15.0


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
