"""Source image resolution use case."""

from __future__ import annotations

from learning_engine.application.ports import HttpFetcher, SourceImageProvider
from learning_engine.domain.models import SourceType


class SourceImageProviderError(Exception):
    """A known provider-side reason that source image metadata is unavailable."""


class SourceImageConfigurationError(SourceImageProviderError):
    """Local or source configuration prevents source image lookup."""


class SourceImageProviderUnavailableError(SourceImageProviderError):
    """A provider 5xx response prevents source image lookup."""


async def resolve_source_image(
    source_type: SourceType,
    source_url: str,
    http_fetcher: HttpFetcher,
    source_image_provider: SourceImageProvider,
) -> str | None:
    """Resolve a source image URL through the configured provider boundary."""

    return await source_image_provider.resolve_source_image(source_type, source_url, http_fetcher)
