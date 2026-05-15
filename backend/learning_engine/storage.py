"""JSON-backed interest persistence."""

from __future__ import annotations

import json
from pathlib import Path

from learning_engine.config import INTERESTS_FILE
from learning_engine.models import Interest, InterestSource, InterestsPayload

DEFAULT_DATA = InterestsPayload(
    interests=[
        Interest(
            id="typescript",
            name="TypeScript",
            description="Track language/compiler updates and important release announcements.",
            priority="high",
            sources=[
                InterestSource(
                    id="typescript-official-site",
                    label="Official site",
                    type="page",
                    url="https://www.typescriptlang.org/",
                ),
                InterestSource(
                    id="typescript-dev-blog",
                    label="TypeScript dev blog",
                    type="feed",
                    url="https://devblogs.microsoft.com/typescript/feed/",
                ),
            ],
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
        interests=[Interest.model_validate(item) for item in interests if isinstance(item, dict)]
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
