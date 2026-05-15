"""Application settings and filesystem locations."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
DATA_DIR = ROOT / "data"
INTERESTS_FILE = DATA_DIR / "interests.json"
HOST = "127.0.0.1"
PORT = 8765
USER_AGENT = "LearningEngine/0.3"
