"""Application settings and filesystem locations."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
WEBAPP_DIR = PROJECT_ROOT / "webapp"
PUBLIC_DIR = WEBAPP_DIR / "dist"
DATA_DIR = BACKEND_ROOT / "data"
INTERESTS_FILE = DATA_DIR / "interests.json"
HOST = "127.0.0.1"
PORT = 8765
USER_AGENT = "LearningEngine/0.3"


def twitter_bearer_token() -> str | None:
    token = os.getenv("TWITTER_BEARER_TOKEN") or os.getenv("X_BEARER_TOKEN")
    return token.strip() if token else None


def spotify_bearer_token() -> str | None:
    token = os.getenv("SPOTIFY_BEARER_TOKEN") or os.getenv("SPOTIFY_ACCESS_TOKEN")
    return token.strip() if token else None
