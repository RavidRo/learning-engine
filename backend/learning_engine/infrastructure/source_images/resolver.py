"""Source image metadata dispatcher."""

from __future__ import annotations

from learning_engine.domain.source_types import SourceType
from learning_engine.infrastructure.fetching import Fetcher
from learning_engine.infrastructure.source_collectors.feed import resolve_feed_image
from learning_engine.infrastructure.source_collectors.page import resolve_page_image
from learning_engine.infrastructure.source_collectors.spotify import resolve_spotify_image
from learning_engine.infrastructure.source_collectors.youtube import resolve_youtube_image


async def resolve_source_image(
    source_type: SourceType,
    source_url: str,
    http_fetcher: Fetcher,
) -> str | None:
    """Resolve a source image URL or raise a classified resolver error."""

    if source_type == "twitter_account":
        return None
    if source_type == "youtube_channel":
        return await resolve_youtube_image(source_url, http_fetcher.fetch_url)
    if source_type == "spotify_podcast":
        return await resolve_spotify_image(source_url, http_fetcher.fetch_json)
    if source_type == "feed":
        return await resolve_feed_image(source_url, http_fetcher.fetch_url)
    return await resolve_page_image(source_url, http_fetcher.fetch_url)


class SourceImageResolver:
    def __init__(self, http_fetcher: Fetcher) -> None:
        self.http_fetcher = http_fetcher

    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
    ) -> str | None:
        return await resolve_source_image(source_type, source_url, self.http_fetcher)
