"""Application-layer ports for external behavior."""

from __future__ import annotations

from typing import Protocol

from learning_engine.domain.interests import InterestSource, InterestsPayload
from learning_engine.domain.source_types import SourceType
from learning_engine.domain.updates import SourceUpdate


class InterestRepository(Protocol):
    def ensure_data_file(self) -> None: ...

    def read_interests(self) -> InterestsPayload: ...

    def write_interests(self, payload: InterestsPayload) -> None: ...


class SourceUpdateCollector(Protocol):
    async def collect_source_updates(self, source: InterestSource) -> list[SourceUpdate]: ...


class SourceImageProvider(Protocol):
    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
    ) -> str | None: ...
