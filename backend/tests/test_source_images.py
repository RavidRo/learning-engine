from __future__ import annotations

from collections.abc import Mapping

import httpx
import pytest

from learning_engine.source_images import (
    SourceImageConfigurationError,
    SourceImageProviderUnavailableError,
    resolve_source_image,
)

HTTP_BAD_REQUEST = 400
HTTP_SERVER_ERROR = 503


async def unused_fetch(url: str) -> bytes:
    raise AssertionError(f"Unexpected byte fetch: {url}")


async def unused_fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
    raise AssertionError(f"Unexpected JSON fetch: {url} {headers}")


@pytest.mark.anyio
async def test_resolve_youtube_image_uses_channel_page_metadata() -> None:
    called_urls: list[str] = []

    async def fetch(url: str) -> bytes:
        called_urls.append(url)
        return b"""<html><meta property="og:image" content="https://yt.example/avatar.jpg"></html>"""

    result = await resolve_source_image("youtube_channel", "@example", fetch, unused_fetch_json)

    assert called_urls == ["https://www.youtube.com/@example"]
    assert result == "https://yt.example/avatar.jpg"


@pytest.mark.anyio
async def test_resolve_spotify_image_uses_show_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPOTIFY_BEARER_TOKEN", "spotify-token")
    called: list[tuple[str, Mapping[str, str]]] = []

    async def fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
        called.append((url, headers))
        return {"images": [{"url": "https://i.scdn.co/image/show"}]}

    result = await resolve_source_image(
        "spotify_podcast",
        "https://open.spotify.com/show/show-one",
        unused_fetch,
        fetch_json,
    )

    assert called == [
        (
            "https://api.spotify.com/v1/shows/show-one?market=US",
            {"Authorization": "Bearer spotify-token"},
        )
    ]
    assert result == "https://i.scdn.co/image/show"


@pytest.mark.anyio
async def test_resolve_spotify_image_raises_configuration_error_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SPOTIFY_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("SPOTIFY_ACCESS_TOKEN", raising=False)

    with pytest.raises(SourceImageConfigurationError, match="Spotify bearer token is not configured"):
        await resolve_source_image(
            "spotify_podcast",
            "https://open.spotify.com/show/show-one",
            unused_fetch,
            unused_fetch_json,
        )


@pytest.mark.anyio
async def test_resolve_feed_image_uses_feed_logo() -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <logo>/assets/feed-logo.png</logo>
        </feed>"""

    result = await resolve_source_image("feed", "https://example.com/feed.xml", fetch, unused_fetch_json)

    assert result == "https://example.com/assets/feed-logo.png"


@pytest.mark.anyio
async def test_resolve_page_image_uses_relative_open_graph_image() -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<html><meta content="/images/card.png" property="og:image"></html>"""

    result = await resolve_source_image("page", "https://example.com/news", fetch, unused_fetch_json)

    assert result == "https://example.com/images/card.png"


@pytest.mark.anyio
async def test_resolve_page_image_falls_back_to_icon() -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<html><link href="//cdn.example.com/icon.png" rel="icon"></html>"""

    result = await resolve_source_image("page", "https://example.com/news", fetch, unused_fetch_json)

    assert result == "https://cdn.example.com/icon.png"


def _http_status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://example.com/news")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("provider response failed", request=request, response=response)


@pytest.mark.anyio
async def test_resolve_source_image_raises_provider_unavailable_for_5xx() -> None:
    async def fetch(_url: str) -> bytes:
        raise _http_status_error(HTTP_SERVER_ERROR)

    with pytest.raises(SourceImageProviderUnavailableError, match="Page metadata provider is unavailable"):
        await resolve_source_image("page", "https://example.com/news", fetch, unused_fetch_json)


@pytest.mark.anyio
async def test_resolve_source_image_raises_http_error_for_4xx() -> None:
    async def fetch(_url: str) -> bytes:
        raise _http_status_error(HTTP_BAD_REQUEST)

    with pytest.raises(httpx.HTTPStatusError, match="provider response failed"):
        await resolve_source_image("page", "https://example.com/news", fetch, unused_fetch_json)


@pytest.mark.anyio
async def test_resolve_source_image_raises_transport_errors() -> None:
    async def fetch(_url: str) -> bytes:
        raise httpx.ConnectError("network down")

    with pytest.raises(httpx.ConnectError, match="network down"):
        await resolve_source_image("page", "https://example.com/news", fetch, unused_fetch_json)


@pytest.mark.anyio
async def test_resolve_source_image_raises_os_errors() -> None:
    async def fetch(_url: str) -> bytes:
        raise OSError("unexpected filesystem edge")

    with pytest.raises(OSError, match="unexpected filesystem edge"):
        await resolve_source_image("page", "https://example.com/news", fetch, unused_fetch_json)


@pytest.mark.anyio
async def test_resolve_source_image_returns_null_on_provider_miss() -> None:
    async def fetch(_url: str) -> bytes:
        return b"<html><head></head><body>No image metadata</body></html>"

    result = await resolve_source_image("page", "https://example.com/news", fetch, unused_fetch_json)

    assert result is None


@pytest.mark.anyio
async def test_resolve_source_image_raises_internal_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_resolver(_source_url: str, _fetch: object) -> str | None:
        raise KeyError("unexpected shape")

    monkeypatch.setattr("learning_engine.source_images._resolve_page_image", fail_resolver)

    with pytest.raises(KeyError, match="unexpected shape"):
        await resolve_source_image("page", "https://example.com/news", unused_fetch, unused_fetch_json)
