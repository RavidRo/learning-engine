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


class InterestStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def ensure_data_file(self) -> None:
        self.path.parent.mkdir(exist_ok=True)
        if not self.path.exists():
            self.write_interests(DEFAULT_DATA)

    def read_interests(self) -> InterestsPayload:
        self.ensure_data_file()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        interests = payload.get("interests", []) if isinstance(payload, dict) else []
        normalized = InterestsPayload(
            interests=[Interest.model_validate(item) for item in interests if isinstance(item, dict)]
        )
        if normalized.model_dump(mode="json", by_alias=True) != payload:
            self.write_interests(normalized)
        return normalized

    def write_interests(self, payload: InterestsPayload) -> None:
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(
            json.dumps(payload.model_dump(mode="json", by_alias=True), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


DEFAULT_STORE = InterestStore(INTERESTS_FILE)


def ensure_data_file() -> None:
    DEFAULT_STORE.ensure_data_file()


def read_interests() -> InterestsPayload:
    return DEFAULT_STORE.read_interests()


def write_interests(payload: InterestsPayload) -> None:
    DEFAULT_STORE.write_interests(payload)
