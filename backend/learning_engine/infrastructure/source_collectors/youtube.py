"""YouTube channel collection through the public channel Atom feed."""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import cast
from urllib.parse import parse_qs, urlparse

from learning_engine.application.resolve_source_image import SourceImageConfigurationError
from learning_engine.config import YOUTUBE_FEED_URL
from learning_engine.domain.updates import SourceUpdate
from learning_engine.infrastructure.source_collectors.feed import parse_feed_items
from learning_engine.infrastructure.source_collectors.image_metadata import (
    FetchFn,
    fetch_optional_provider_bytes,
    normalized_image_url,
)

CHANNEL_ID_PATTERN = re.compile(r"\bUC[\w-]{20,}\b")
CHANNEL_ID_META_PATTERN = re.compile(
    r"<meta\s+(?:itemprop=[\"']channelId[\"']\s+content|content)=[\"'](UC[\w-]{20,})[\"']",
    re.IGNORECASE,
)
YOUTUBE_INITIAL_DATA_MARKER = "ytInitialData"
AVATAR_KEYS = ("avatar", "avatarViewModel", "channelAvatar", "decoratedAvatarViewModel")


def _channel_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    query_channel_id = parse_qs(parsed.query).get("channel_id")
    if query_channel_id:
        return query_channel_id[0]

    match = CHANNEL_ID_PATTERN.search(parsed.path)
    return match.group(0) if match else None


def _extract_channel_id(html: bytes) -> str:
    decoded = html.decode("utf-8", errors="replace")
    meta_match = CHANNEL_ID_META_PATTERN.search(decoded)
    if meta_match:
        return meta_match.group(1)

    match = CHANNEL_ID_PATTERN.search(decoded)
    if match:
        return match.group(0)

    raise ValueError("Could not find a YouTube channel ID in the channel page")


def _json_object_after_marker(decoded: str, marker: str) -> object | None:
    marker_index = decoded.find(marker)
    if marker_index == -1:
        return None

    start = decoded.find("{", marker_index)
    if start == -1:
        return None

    try:
        parsed, _end_index = json.JSONDecoder().raw_decode(decoded[start:])
    except json.JSONDecodeError:
        return None
    return cast(object, parsed)


def _largest_image_url(images: object, base_url: str) -> str | None:
    if not isinstance(images, list):
        return None

    ranked_images: list[tuple[int, str]] = []
    for index, image in enumerate(images):
        if not isinstance(image, dict):
            continue
        image_url = normalized_image_url(cast(str | None, image.get("url")), base_url)
        if image_url is None:
            continue
        width = image.get("width")
        height = image.get("height")
        area = width * height if isinstance(width, int) and isinstance(height, int) else index
        ranked_images.append((area, image_url))

    if not ranked_images:
        return None
    return max(ranked_images, key=lambda item: item[0])[1]


def _image_url_from_avatar(value: object, base_url: str) -> str | None:
    if not isinstance(value, dict):
        return None

    for key in ("thumbnails", "sources"):
        image_url = _largest_image_url(value.get(key), base_url)
        if image_url is not None:
            return image_url

    image = value.get("image")
    if isinstance(image, dict):
        return _image_url_from_avatar(image, base_url)

    return normalized_image_url(cast(str | None, value.get("url")), base_url)


def _find_channel_avatar_image(value: object, base_url: str) -> str | None:
    if isinstance(value, dict):
        for key in AVATAR_KEYS:
            image_url = _image_url_from_avatar(value.get(key), base_url)
            if image_url is not None:
                return image_url

        for child in value.values():
            image_url = _find_channel_avatar_image(child, base_url)
            if image_url is not None:
                return image_url

    if isinstance(value, list):
        for child in value:
            image_url = _find_channel_avatar_image(child, base_url)
            if image_url is not None:
                return image_url

    return None


def _channel_avatar_image_url(html: bytes, base_url: str) -> str | None:
    decoded = html.decode("utf-8", errors="replace")
    initial_data = _json_object_after_marker(decoded, YOUTUBE_INITIAL_DATA_MARKER)
    if initial_data is None:
        return None

    return _find_channel_avatar_image(initial_data, base_url)


def youtube_channel_page_url(source_url: str) -> str:
    stripped = source_url.strip()
    if not stripped:
        raise ValueError("YouTube channel source URL is required")

    channel_id = _channel_id_from_url(stripped) or (stripped if CHANNEL_ID_PATTERN.fullmatch(stripped) else None)
    if channel_id is not None:
        return f"https://www.youtube.com/channel/{channel_id}"

    if stripped.startswith("@"):
        return f"https://www.youtube.com/{stripped}"
    if not urlparse(stripped).scheme:
        return f"https://www.youtube.com/@{stripped.lstrip('@')}"
    return stripped


async def youtube_feed_url(source_url: str, fetch: Callable[[str], Awaitable[bytes]]) -> str:
    stripped = source_url.strip()
    if not stripped:
        raise ValueError("YouTube channel source URL is required")

    channel_id = _channel_id_from_url(stripped) or (stripped if CHANNEL_ID_PATTERN.fullmatch(stripped) else None)
    if channel_id is not None:
        return YOUTUBE_FEED_URL.format(channel_id=channel_id)

    page_url = youtube_channel_page_url(stripped)
    return YOUTUBE_FEED_URL.format(channel_id=_extract_channel_id(await fetch(page_url)))


async def collect_youtube_channel(source_url: str, fetch: Callable[[str], Awaitable[bytes]]) -> list[SourceUpdate]:
    feed_url = await youtube_feed_url(source_url, fetch)
    return parse_feed_items(await fetch(feed_url), watch_keywords=[], ignore_keywords=[])


async def resolve_youtube_image(source_url: str, fetch: FetchFn) -> str | None:
    try:
        page_url = youtube_channel_page_url(source_url)
    except ValueError as exc:
        raise SourceImageConfigurationError("YouTube channel source URL is invalid") from exc
    channel_page = await fetch_optional_provider_bytes(page_url, fetch, "YouTube")
    if channel_page is None:
        return None
    return _channel_avatar_image_url(channel_page, page_url)
