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
USER_AGENT = f"SignalGarden/{APPLICATION_VERSION}"
YOUTUBE_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
X_API_ORIGIN = "https://api.x.com/2"
SPOTIFY_API_ORIGIN = "https://api.spotify.com/v1"
DEFAULT_MCP_ALLOWED_HOSTS = ["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*"]


def twitter_bearer_token() -> str | None:
    token = os.getenv("X_BEARER_TOKEN")
    return token.strip() if token else None


def spotify_bearer_token() -> str | None:
    token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    return token.strip() if token else None


def clerk_issuer() -> str | None:
    issuer = os.getenv("CLERK_ISSUER")
    if issuer is None:
        return None
    normalized = issuer.strip().rstrip("/")
    return normalized or None


def clerk_jwks_url() -> str | None:
    configured_url = os.getenv("CLERK_JWKS_URL")
    if configured_url is not None:
        normalized = configured_url.strip()
        return normalized or None
    issuer = clerk_issuer()
    if issuer is None:
        return None
    return f"{issuer}/.well-known/jwks.json"


def clerk_authorized_parties() -> list[str]:
    parties = os.getenv("CLERK_AUTHORIZED_PARTIES")
    if parties is None:
        return []
    return [party for candidate in parties.split(",") if (party := candidate.strip())]


def mcp_allowed_origins() -> list[str]:
    origins = os.getenv("MCP_ALLOWED_ORIGINS")
    if origins is None:
        return []
    return [origin for candidate in origins.split(",") if (origin := candidate.strip())]


def mcp_allowed_hosts() -> list[str]:
    hosts = os.getenv("MCP_ALLOWED_HOSTS")
    if hosts is None:
        return DEFAULT_MCP_ALLOWED_HOSTS
    configured_hosts = [host for candidate in hosts.split(",") if (host := candidate.strip())]
    return [*DEFAULT_MCP_ALLOWED_HOSTS, *configured_hosts]
