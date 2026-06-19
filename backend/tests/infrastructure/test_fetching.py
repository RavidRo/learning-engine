from __future__ import annotations

import asyncio
from collections.abc import Mapping

import pytest
from cachetools import TTLCache

from learning_engine.infrastructure.fetching import CachedFetcher

EXPECTED_OTHER_JSON_CALL = 2


class StubFetcher:
    def __init__(self) -> None:
        self.byte_calls: list[str] = []
        self.json_calls: list[tuple[str, Mapping[str, str]]] = []
        self.fail_next_byte = False

    async def fetch_url(self, url: str) -> bytes:
        self.byte_calls.append(url)
        if self.fail_next_byte:
            self.fail_next_byte = False
            raise OSError("network down")
        return f"bytes:{len(self.byte_calls)}:{url}".encode()

    async def fetch_json(self, url: str, headers: Mapping[str, str]) -> dict[str, object]:
        self.json_calls.append((url, headers))
        return {"call": len(self.json_calls), "url": url}


class SlowStubFetcher(StubFetcher):
    async def fetch_url(self, url: str) -> bytes:
        self.byte_calls.append(url)
        await asyncio.sleep(0.01)
        return b"shared"


def _cached_fetcher(fetcher: StubFetcher) -> CachedFetcher:
    return CachedFetcher(fetcher, TTLCache(maxsize=16, ttl=300))


@pytest.mark.anyio
async def test_cached_fetcher_reuses_successful_byte_responses() -> None:
    fetcher = StubFetcher()
    cached_fetcher = _cached_fetcher(fetcher)

    first = await cached_fetcher.fetch_url("https://example.com/feed.xml")
    second = await cached_fetcher.fetch_url("https://example.com/feed.xml")

    assert first == b"bytes:1:https://example.com/feed.xml"
    assert second == first
    assert fetcher.byte_calls == ["https://example.com/feed.xml"]


@pytest.mark.anyio
async def test_cached_fetcher_coalesces_concurrent_byte_responses() -> None:
    fetcher = SlowStubFetcher()
    cached_fetcher = _cached_fetcher(fetcher)

    first, second = await asyncio.gather(
        cached_fetcher.fetch_url("https://example.com/feed.xml"),
        cached_fetcher.fetch_url("https://example.com/feed.xml"),
    )

    assert first == b"shared"
    assert second == b"shared"
    assert fetcher.byte_calls == ["https://example.com/feed.xml"]


@pytest.mark.anyio
async def test_cached_fetcher_separates_bytes_json_and_headers() -> None:
    fetcher = StubFetcher()
    cached_fetcher = _cached_fetcher(fetcher)

    byte_response = await cached_fetcher.fetch_url("https://example.com/resource")
    first_json = await cached_fetcher.fetch_json("https://example.com/resource", {"Authorization": "Bearer one"})
    repeated_json = await cached_fetcher.fetch_json("https://example.com/resource", {"Authorization": "Bearer one"})
    other_json = await cached_fetcher.fetch_json("https://example.com/resource", {"Authorization": "Bearer two"})

    assert byte_response == b"bytes:1:https://example.com/resource"
    assert first_json == repeated_json
    assert other_json["call"] == EXPECTED_OTHER_JSON_CALL
    assert fetcher.byte_calls == ["https://example.com/resource"]
    assert fetcher.json_calls == [
        ("https://example.com/resource", {"Authorization": "Bearer one"}),
        ("https://example.com/resource", {"Authorization": "Bearer two"}),
    ]


@pytest.mark.anyio
async def test_cached_fetcher_does_not_cache_failed_fetches() -> None:
    fetcher = StubFetcher()
    cached_fetcher = _cached_fetcher(fetcher)
    fetcher.fail_next_byte = True

    with pytest.raises(OSError, match="network down"):
        await cached_fetcher.fetch_url("https://example.com/feed.xml")

    response = await cached_fetcher.fetch_url("https://example.com/feed.xml")

    assert response == b"bytes:2:https://example.com/feed.xml"
    assert fetcher.byte_calls == [
        "https://example.com/feed.xml",
        "https://example.com/feed.xml",
    ]
