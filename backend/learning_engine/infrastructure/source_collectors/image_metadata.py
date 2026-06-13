"""Shared helpers for resolving source image metadata."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast
from urllib.parse import urljoin, urlparse

import httpx

from learning_engine.application.resolve_source_image import (
    SourceImageProviderUnavailableError,
)
from learning_engine.common.text import strip_markup

FetchFn = Callable[[str], Awaitable[bytes]]
JsonFetchFn = Callable[[str, Mapping[str, str]], Awaitable[dict[str, object]]]

TAG_PATTERN = re.compile(r"<(?:meta|link)\b[^>]*>", re.IGNORECASE)
IMG_TAG_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
ATTRIBUTE_PATTERN = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*['\"]([^'\"]*)['\"]")

SERVER_ERROR_STATUS_MIN = 500
SERVER_ERROR_STATUS_MAX = 599


def _is_provider_server_error(exc: httpx.HTTPStatusError) -> bool:
    return SERVER_ERROR_STATUS_MIN <= exc.response.status_code <= SERVER_ERROR_STATUS_MAX


async def fetch_provider_bytes(url: str, fetch: FetchFn, provider: str) -> bytes:
    try:
        return await fetch(url)
    except httpx.HTTPStatusError as exc:
        if _is_provider_server_error(exc):
            raise SourceImageProviderUnavailableError(f"{provider} metadata provider is unavailable") from exc
        raise


async def fetch_provider_json(
    url: str,
    headers: Mapping[str, str],
    fetch_json: JsonFetchFn,
    provider: str,
) -> dict[str, object]:
    try:
        return await fetch_json(url, headers)
    except httpx.HTTPStatusError as exc:
        if _is_provider_server_error(exc):
            raise SourceImageProviderUnavailableError(f"{provider} metadata provider is unavailable") from exc
        raise


def normalized_image_url(image_url: str | None, base_url: str) -> str | None:
    stripped = str(image_url or "").strip()
    if not stripped:
        return None
    if stripped.startswith("//"):
        parsed = urlparse(base_url)
        scheme = parsed.scheme or "https"
        return f"{scheme}:{stripped}"
    return urljoin(base_url, stripped)


def first_feed_image(feed: Mapping[str, Any], base_url: str) -> str | None:
    image = feed.get("image")
    if isinstance(image, Mapping):
        for key in ("href", "url", "link"):
            resolved = normalized_image_url(cast(str | None, image.get(key)), base_url)
            if resolved is not None:
                return resolved

    for key in ("icon", "logo"):
        resolved = normalized_image_url(cast(str | None, feed.get(key)), base_url)
        if resolved is not None:
            return resolved
    return None


def html_image_url(html: bytes, base_url: str) -> str | None:
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
            resolved = normalized_image_url(strip_markup(image_url), base_url)
            if resolved is not None:
                return resolved
    return None


def first_html_img_src(value: object, base_url: str) -> str | None:
    if value is None:
        return None
    for tag_match in IMG_TAG_PATTERN.finditer(str(value)):
        attributes = {key.lower(): attr_value for key, attr_value in ATTRIBUTE_PATTERN.findall(tag_match.group(0))}
        resolved = normalized_image_url(strip_markup(attributes.get("src")), base_url)
        if resolved is not None:
            return resolved
    return None
