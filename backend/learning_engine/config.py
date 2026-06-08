"""Application settings and filesystem locations."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"
INTERESTS_FILE = DATA_DIR / "interests.json"
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
