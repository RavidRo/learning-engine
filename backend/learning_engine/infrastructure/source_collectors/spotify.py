"""Spotify podcast collection through the Spotify Web API."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast
from urllib.parse import quote, urlparse

from learning_engine.application.resolve_source_image import SourceImageConfigurationError, SourceImageProviderError
from learning_engine.common.dates import parse_datetime
from learning_engine.common.text import strip_markup
from learning_engine.config import SPOTIFY_API_ORIGIN, spotify_bearer_token
from learning_engine.domain.updates import SourceUpdate
from learning_engine.infrastructure.source_collectors.image_metadata import (
    JsonFetchFn,
    fetch_provider_json,
    normalized_image_url,
)

SPOTIFY_SHOW_PATH_PARTS = 2


def spotify_show_id(source_url: str) -> str:
    stripped = source_url.strip()
    if not stripped:
        raise ValueError("Spotify podcast source URL is required")

    if stripped.startswith("spotify:show:"):
        return stripped.removeprefix("spotify:show:")

    parsed = urlparse(stripped)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc and len(parts) >= SPOTIFY_SHOW_PATH_PARTS and parts[0] == "show":
        return parts[1]

    return stripped


def _headers() -> Mapping[str, str]:
    token = spotify_bearer_token()
    if token is None:
        raise ValueError("Spotify bearer token is required for spotify_podcast sources")
    return {"Authorization": f"Bearer {token}"}


def _episode_url(episode: Mapping[str, object]) -> str | None:
    external_urls = episode.get("external_urls")
    if isinstance(external_urls, dict):
        spotify_url = external_urls.get("spotify")
        if isinstance(spotify_url, str) and spotify_url.strip():
            return spotify_url

    href = episode.get("href")
    return href if isinstance(href, str) and href.strip() else None


def _episode_update(episode: Mapping[str, object]) -> SourceUpdate:
    release_date = str(episode.get("release_date") or "").strip() or None
    summary = strip_markup(episode.get("description")) or strip_markup(episode.get("html_description"))
    published_at = parse_datetime(release_date)
    return SourceUpdate(
        title=strip_markup(episode.get("name")),
        url=_episode_url(episode),
        summary=summary,
        published=published_at,
        published_at=published_at,
    )


async def collect_spotify_podcast(source_url: str, fetch_json: JsonFetchFn) -> list[SourceUpdate]:
    show_id = spotify_show_id(source_url)
    response = await fetch_json(
        f"{SPOTIFY_API_ORIGIN}/shows/{quote(show_id)}/episodes?limit=20&market=US",
        _headers(),
    )
    episodes = response.get("items", [])
    if not isinstance(episodes, list):
        return []

    return [_episode_update(cast(Mapping[str, Any], episode)) for episode in episodes if isinstance(episode, dict)]


async def resolve_spotify_image(source_url: str, fetch_json: JsonFetchFn) -> str | None:
    token = spotify_bearer_token()
    if token is None:
        raise SourceImageConfigurationError("Spotify bearer token is not configured")

    try:
        show_id = spotify_show_id(source_url)
    except ValueError as exc:
        raise SourceImageConfigurationError("Spotify podcast source URL is invalid") from exc

    response = await fetch_provider_json(
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
        resolved = normalized_image_url(cast(str | None, image.get("url")), "https://open.spotify.com/")
        if resolved is not None:
            return resolved
    return None
