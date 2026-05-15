"""Application settings and filesystem locations."""

from __future__ import annotations

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
