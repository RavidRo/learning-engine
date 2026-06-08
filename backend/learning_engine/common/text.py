"""Text normalization and keyword matching."""

from __future__ import annotations

import re
from html import unescape


def strip_markup(value: object) -> str | None:
    if value is None:
        return None
    stripped = re.sub(r"<[^>]+>", "", unescape(str(value)))
    normalized = re.sub(r"\s+", " ", stripped).strip()
    return normalized or None


def keyword_matches(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def searchable_text(*values: object) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            continue
        stripped = str(value).strip()
        if stripped:
            parts.append(stripped)
    return " ".join(parts)
