"""Application settings and filesystem locations."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from tomllib import TOMLDecodeError, loads

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"
INTERESTS_FILE = DATA_DIR / "interests.json"
HOST = "127.0.0.1"
PORT = 8765
DEFAULT_APPLICATION_VERSION = "0.0.0"
logger = logging.getLogger(__name__)


def _read_application_version() -> str:
    try:
        version = loads((BACKEND_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    except (FileNotFoundError, TOMLDecodeError, KeyError, TypeError) as exc:
        logger.warning(
            "Could not read application version from pyproject.toml; using default.",
            extra={"reason": str(exc)},
        )
        return DEFAULT_APPLICATION_VERSION
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Unexpected error reading application version from pyproject.toml; using default.",
            extra={"reason": str(exc)},
        )
        return DEFAULT_APPLICATION_VERSION
    return str(version)


APPLICATION_VERSION = _read_application_version()
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
