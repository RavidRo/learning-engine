"""Spotify podcast collection through the Spotify Web API."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast
from urllib.parse import quote, urlparse

from learning_engine.config import spotify_bearer_token
from learning_engine.dates import format_datetime, parse_datetime
from learning_engine.models import CollectedUpdate
from learning_engine.text import strip_markup

JsonFetchFn = Callable[[str, Mapping[str, str]], dict[str, object]]
SPOTIFY_API_ORIGIN = "https://api.spotify.com/v1"
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


def _episode_update(episode: Mapping[str, object]) -> CollectedUpdate:
    release_date = str(episode.get("release_date") or "").strip() or None
    summary = strip_markup(episode.get("description")) or strip_markup(episode.get("html_description"))
    return CollectedUpdate(
        title=strip_markup(episode.get("name")),
        url=_episode_url(episode),
        summary=summary,
        published=release_date,
        published_at=format_datetime(parse_datetime(release_date)),
    )


def collect_spotify_podcast(source_url: str, fetch_json: JsonFetchFn) -> list[CollectedUpdate]:
    show_id = spotify_show_id(source_url)
    response = fetch_json(
        f"{SPOTIFY_API_ORIGIN}/shows/{quote(show_id)}/episodes?limit=20&market=US",
        _headers(),
    )
    episodes = response.get("items", [])
    if not isinstance(episodes, list):
        return []

    return [_episode_update(cast(Mapping[str, Any], episode)) for episode in episodes if isinstance(episode, dict)]
