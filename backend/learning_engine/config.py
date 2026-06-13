"""Application settings and filesystem locations."""

from __future__ import annotations

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://learning_engine:learning_engine@localhost:5432/learning_engine",
)
HOST = "127.0.0.1"
PORT = 8765
APPLICATION_VERSION = "0.1.0"
USER_AGENT = f"LearningEngine/{APPLICATION_VERSION}"
YOUTUBE_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
X_API_ORIGIN = "https://api.x.com/2"
SPOTIFY_API_ORIGIN = "https://api.spotify.com/v1"


def twitter_bearer_token() -> str | None:
    token = os.getenv("X_BEARER_TOKEN")
    return token.strip() if token else None


def spotify_bearer_token() -> str | None:
    token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    return token.strip() if token else None


def mcp_auth_token() -> str | None:
    token = os.getenv("MCP_AUTH_TOKEN")
    if token is None:
        return None
    stripped = token.strip()
    return stripped or None


def mcp_allowed_origins() -> list[str]:
    origins = os.getenv("MCP_ALLOWED_ORIGINS")
    if origins is None:
        return []
    return [origin for candidate in origins.split(",") if (origin := candidate.strip())]
