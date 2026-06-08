"""Application-layer ports for external behavior."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from learning_engine.domain.models import CollectedUpdate, InterestSource, InterestsPayload, SourceType


class HttpFetcher(Protocol):
    async def fetch_url(self, url: str) -> bytes: ...

    async def fetch_json(self, url: str, headers: Mapping[str, str]) -> dict[str, object]: ...


class InterestRepository(Protocol):
    def ensure_data_file(self) -> None: ...

    def read_interests(self) -> InterestsPayload: ...

    def write_interests(self, payload: InterestsPayload) -> None: ...


class SourceUpdateCollector(Protocol):
    async def collect_source_updates(
        self,
        source: InterestSource,
        http_fetcher: HttpFetcher,
    ) -> list[CollectedUpdate]: ...


class SourceImageProvider(Protocol):
    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
        http_fetcher: HttpFetcher,
    ) -> str | None: ...
