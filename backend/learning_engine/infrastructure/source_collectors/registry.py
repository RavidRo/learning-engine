"""Infrastructure dispatcher for supported source update collectors."""

from __future__ import annotations

from learning_engine.application.ports import HttpFetcher
from learning_engine.domain.interests import InterestSource
from learning_engine.domain.updates import SourceUpdate
from learning_engine.infrastructure.source_collectors.feed import parse_feed_items
from learning_engine.infrastructure.source_collectors.page import parse_page_items
from learning_engine.infrastructure.source_collectors.spotify import (
    collect_spotify_podcast,
)
from learning_engine.infrastructure.source_collectors.twitter import (
    collect_twitter_account,
)
from learning_engine.infrastructure.source_collectors.youtube import (
    collect_youtube_channel,
)


class SourceUpdateCollectorRegistry:
    def __init__(self, http_fetcher: HttpFetcher) -> None:
        self.http_fetcher = http_fetcher

    async def collect_source_updates(
        self,
        source: InterestSource,
    ) -> list[SourceUpdate]:
        if source.type == "feed":
            return parse_feed_items(
                await self.http_fetcher.fetch_url(source.url),
                watch_keywords=[],
                ignore_keywords=source.ignore_keywords,
            )

        if source.type == "page":
            return parse_page_items(
                await self.http_fetcher.fetch_url(source.url),
                source.url,
                watch_keywords=[],
                ignore_keywords=source.ignore_keywords,
            )

        if source.type == "youtube_channel":
            return await collect_youtube_channel(source.url, self.http_fetcher.fetch_url)

        if source.type == "twitter_account":
            return await collect_twitter_account(source.url, self.http_fetcher.fetch_json)

        return await collect_spotify_podcast(source.url, self.http_fetcher.fetch_json)
