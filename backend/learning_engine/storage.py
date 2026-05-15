"""JSON-backed interest persistence."""

from __future__ import annotations

import json
from pathlib import Path

from learning_engine.config import INTERESTS_FILE
from learning_engine.models import InterestsPayload, TechnologyInterest

DEFAULT_DATA = InterestsPayload(
    interests=[
        TechnologyInterest(
            id="typescript",
            name="TypeScript",
            priority="high",
            official_site_url="https://www.typescriptlang.org/",
            official_feed_url="https://devblogs.microsoft.com/typescript/feed/",
            watch_keywords=["release", "beta", "rc", "compiler", "breaking change", "typescript 5"],
            ignore_keywords=["webinar", "case study"],
            notes="Notify me about language/compiler updates and important release announcements.",
            enabled=True,
        )
    ]
)


def ensure_data_file(path: Path = INTERESTS_FILE) -> None:
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        write_interests(DEFAULT_DATA, path)


def read_interests(path: Path = INTERESTS_FILE) -> InterestsPayload:
    ensure_data_file(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    interests = payload.get("interests", []) if isinstance(payload, dict) else []
    normalized = InterestsPayload(
        interests=[TechnologyInterest.model_validate(item) for item in interests if isinstance(item, dict)]
    )
    if normalized.model_dump(mode="json", by_alias=True) != payload:
        write_interests(normalized, path)
    return normalized


def write_interests(payload: InterestsPayload, path: Path = INTERESTS_FILE) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(payload.model_dump(mode="json", by_alias=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
