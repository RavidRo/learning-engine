#!/usr/bin/env python3
"""Compatibility entrypoint for the FastAPI backend.

Run:
    task run
Open:
    http://localhost:8765
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from learning_engine.app import app, run
from learning_engine.collector import collect_updates as _collect_updates
from learning_engine.collector import parse_feed_items as _parse_feed_items
from learning_engine.collector import parse_page_items as _parse_page_items
from learning_engine.fetching import fetch_url
from learning_engine.models import Interest, InterestsPayload
from learning_engine.storage import DEFAULT_DATA as _DEFAULT_DATA
from learning_engine.storage import ensure_data_file
from learning_engine.storage import read_interests as _read_interests
from learning_engine.storage import write_interests as _write_interests

DEFAULT_DATA = _DEFAULT_DATA.model_dump(mode="json", by_alias=True)
__all__ = ["app"]


def normalize_interest(item: dict[str, Any]) -> dict[str, Any]:
    return Interest.model_validate(item).model_dump(mode="json", by_alias=True)


def read_interests() -> dict[str, Any]:
    return _read_interests().model_dump(mode="json", by_alias=True)


def write_interests(payload: dict[str, Any]) -> None:
    _write_interests(InterestsPayload.model_validate(payload))


def parse_feed_items(
    feed_bytes: bytes,
    watch_keywords: list[str] | None = None,
    ignore_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    return [
        item.model_dump(mode="json")
        for item in _parse_feed_items(feed_bytes, watch_keywords=watch_keywords, ignore_keywords=ignore_keywords)
    ]


def parse_page_items(
    page_bytes: bytes,
    page_url: str,
    watch_keywords: list[str] | None = None,
    ignore_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    return [
        item.model_dump(mode="json")
        for item in _parse_page_items(
            page_bytes,
            page_url,
            watch_keywords=watch_keywords,
            ignore_keywords=ignore_keywords,
        )
    ]


def collect_updates(
    payload: dict[str, Any],
    days: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    return _collect_updates(
        InterestsPayload.model_validate(payload),
        days=days,
        now=now,
        fetch=fetch_url,
    ).model_dump(mode="json", by_alias=True)


def main() -> None:
    ensure_data_file()
    run()


if __name__ == "__main__":
    main()
