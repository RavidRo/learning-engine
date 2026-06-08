"""Best-effort source image metadata resolution."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, NoReturn, cast
from urllib.parse import quote, urljoin, urlparse

import feedparser
import httpx

from learning_engine.application.ports import HttpFetcher
from learning_engine.application.resolve_source_image import (
    SourceImageConfigurationError,
    SourceImageProviderError,
    SourceImageProviderUnavailableError,
)
from learning_engine.common.text import strip_markup
from learning_engine.config import spotify_bearer_token
from learning_engine.domain.models import SourceType
from learning_engine.infrastructure.source_collectors.spotify import SPOTIFY_API_ORIGIN, spotify_show_id
from learning_engine.infrastructure.source_collectors.youtube import youtube_channel_page_url

FetchFn = Callable[[str], Awaitable[bytes]]
JsonFetchFn = Callable[[str, Mapping[str, str]], Awaitable[dict[str, object]]]

TAG_PATTERN = re.compile(r"<(?:meta|link)\b[^>]*>", re.IGNORECASE)
ATTRIBUTE_PATTERN = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*['\"]([^'\"]*)['\"]")


SERVER_ERROR_STATUS_MIN = 500
SERVER_ERROR_STATUS_MAX = 599


def _raise_configuration_error(message: str, exc: Exception | None = None) -> NoReturn:
    raise SourceImageConfigurationError(message) from exc


def _raise_provider_unavailable_error(message: str, exc: Exception) -> NoReturn:
    raise SourceImageProviderUnavailableError(message) from exc


def _is_provider_server_error(exc: httpx.HTTPStatusError) -> bool:
    return SERVER_ERROR_STATUS_MIN <= exc.response.status_code <= SERVER_ERROR_STATUS_MAX


async def _fetch_provider_bytes(url: str, fetch: FetchFn, provider: str) -> bytes:
    try:
        return await fetch(url)
    except httpx.HTTPStatusError as exc:
        if _is_provider_server_error(exc):
            _raise_provider_unavailable_error(f"{provider} metadata provider is unavailable", exc)
        raise


async def _fetch_provider_json(
    url: str,
    headers: Mapping[str, str],
    fetch_json: JsonFetchFn,
    provider: str,
) -> dict[str, object]:
    try:
        return await fetch_json(url, headers)
    except httpx.HTTPStatusError as exc:
        if _is_provider_server_error(exc):
            _raise_provider_unavailable_error(f"{provider} metadata provider is unavailable", exc)
        raise


def _normalized_image_url(image_url: str | None, base_url: str) -> str | None:
    stripped = str(image_url or "").strip()
    if not stripped:
        return None
    if stripped.startswith("//"):
        parsed = urlparse(base_url)
        scheme = parsed.scheme or "https"
        return f"{scheme}:{stripped}"
    return urljoin(base_url, stripped)


def _first_feed_image(feed: Mapping[str, Any], base_url: str) -> str | None:
    image = feed.get("image")
    if isinstance(image, Mapping):
        for key in ("href", "url", "link"):
            resolved = _normalized_image_url(cast(str | None, image.get(key)), base_url)
            if resolved is not None:
                return resolved

    for key in ("icon", "logo"):
        resolved = _normalized_image_url(cast(str | None, feed.get(key)), base_url)
        if resolved is not None:
            return resolved
    return None


def _html_image_url(html: bytes, base_url: str) -> str | None:
    decoded = html.decode("utf-8", errors="replace")
    for tag_match in TAG_PATTERN.finditer(decoded):
        attributes = {key.lower(): value for key, value in ATTRIBUTE_PATTERN.findall(tag_match.group(0))}
        image_url = None
        if tag_match.group(0).lower().startswith("<meta"):
            marker = (attributes.get("property") or attributes.get("name") or attributes.get("itemprop") or "").lower()
            if marker in {"og:image", "twitter:image", "image"}:
                image_url = attributes.get("content")
        else:
            rel = attributes.get("rel", "").lower()
            if "icon" in rel or "apple-touch-icon" in rel:
                image_url = attributes.get("href")

        if image_url is not None:
            resolved = _normalized_image_url(strip_markup(image_url), base_url)
            if resolved is not None:
                return resolved
    return None


async def _resolve_youtube_image(source_url: str, fetch: FetchFn) -> str | None:
    try:
        page_url = youtube_channel_page_url(source_url)
    except ValueError as exc:
        _raise_configuration_error("YouTube channel source URL is invalid", exc)
    return _html_image_url(await _fetch_provider_bytes(page_url, fetch, "YouTube"), page_url)


async def _resolve_spotify_image(source_url: str, fetch_json: JsonFetchFn) -> str | None:
    token = spotify_bearer_token()
    if token is None:
        raise SourceImageConfigurationError("Spotify bearer token is not configured")

    try:
        show_id = spotify_show_id(source_url)
    except ValueError as exc:
        _raise_configuration_error("Spotify podcast source URL is invalid", exc)

    response = await _fetch_provider_json(
        f"{SPOTIFY_API_ORIGIN}/shows/{quote(show_id)}?market=US",
        {"Authorization": f"Bearer {token}"},
        fetch_json,
        "Spotify",
    )
    images = response.get("images", [])
    if not isinstance(images, list):
        raise SourceImageProviderError("Spotify show metadata did not include an images list")

    for image in images:
        if not isinstance(image, Mapping):
            continue
        resolved = _normalized_image_url(cast(str | None, image.get("url")), "https://open.spotify.com/")
        if resolved is not None:
            return resolved
    return None


async def _resolve_feed_image(source_url: str, fetch: FetchFn) -> str | None:
    feed_bytes = await _fetch_provider_bytes(source_url, fetch, "Feed")
    parsed = feedparser.parse(feed_bytes)
    feed = parsed.get("feed", {})
    if isinstance(feed, Mapping):
        resolved = _first_feed_image(cast(Mapping[str, Any], feed), source_url)
        if resolved is not None:
            return resolved
    return _html_image_url(feed_bytes, source_url)


async def _resolve_page_image(source_url: str, fetch: FetchFn) -> str | None:
    return _html_image_url(await _fetch_provider_bytes(source_url, fetch, "Page"), source_url)


async def resolve_source_image(
    source_type: SourceType,
    source_url: str,
    http_fetcher: HttpFetcher,
) -> str | None:
    """Resolve a source image URL or raise a classified resolver error."""

    if source_type == "twitter_account":
        return None

    if source_type == "youtube_channel":
        return await _resolve_youtube_image(source_url, http_fetcher.fetch_url)
    if source_type == "spotify_podcast":
        return await _resolve_spotify_image(source_url, http_fetcher.fetch_json)
    if source_type == "feed":
        return await _resolve_feed_image(source_url, http_fetcher.fetch_url)
    return await _resolve_page_image(source_url, http_fetcher.fetch_url)


class SourceImageResolver:
    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
        http_fetcher: HttpFetcher,
    ) -> str | None:
        return await resolve_source_image(source_type, source_url, http_fetcher)
