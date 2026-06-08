"""YouTube channel collection through the public channel Atom feed."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from urllib.parse import parse_qs, urlparse

from learning_engine.domain.models import CollectedUpdate
from learning_engine.infrastructure.source_collectors.feed import parse_feed_items

CHANNEL_ID_PATTERN = re.compile(r"\bUC[\w-]{20,}\b")
CHANNEL_ID_META_PATTERN = re.compile(
    r"<meta\s+(?:itemprop=[\"']channelId[\"']\s+content|content)=[\"'](UC[\w-]{20,})[\"']",
    re.IGNORECASE,
)
YOUTUBE_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


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


async def collect_youtube_channel(source_url: str, fetch: Callable[[str], Awaitable[bytes]]) -> list[CollectedUpdate]:
    feed_url = await youtube_feed_url(source_url, fetch)
    return parse_feed_items(await fetch(feed_url), watch_keywords=[], ignore_keywords=[])
