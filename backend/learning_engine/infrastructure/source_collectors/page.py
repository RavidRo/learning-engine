"""Best-effort official-page parsing for sources without feeds."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from learning_engine.common.dates import parse_datetime
from learning_engine.common.text import keyword_matches, searchable_text, strip_markup
from learning_engine.domain.updates import SourceUpdate
from learning_engine.infrastructure.source_collectors.image_metadata import (
    FetchFn,
    fetch_provider_bytes,
    html_image_url,
)

MIN_PAGE_LINK_TITLE_LENGTH = 8
PAGE_LINK_CONTEXT_CHARS = 500
LINK_PATTERN = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
DATE_PATTERNS = (
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}",
        re.IGNORECASE,
    ),
)


def _decode_html(page_bytes: bytes) -> str:
    return page_bytes.decode("utf-8", errors="replace")


def _same_origin(url: str, page_url: str) -> bool:
    parsed_url = urlparse(url)
    return not parsed_url.netloc or parsed_url.netloc == urlparse(page_url).netloc


def _nearby_context(html: str, start: int, end: int) -> str | None:
    return strip_markup(html[max(0, start - PAGE_LINK_CONTEXT_CHARS) : end + PAGE_LINK_CONTEXT_CHARS])


def _published_from_context(context: str | None) -> str | None:
    if context is None:
        return None
    for date_pattern in DATE_PATTERNS:
        date_match = date_pattern.search(context)
        if date_match:
            return date_match.group(0)
    return None


def parse_page_items(
    page_bytes: bytes,
    page_url: str,
    watch_keywords: list[str],
    ignore_keywords: list[str],
) -> list[SourceUpdate]:
    """Extract linked update-like items from an official page fallback."""

    html = _decode_html(page_bytes)
    updates: list[SourceUpdate] = []
    seen: set[str] = set()

    for match in LINK_PATTERN.finditer(html):
        href, body = match.groups()
        title = strip_markup(body)
        if title is None or len(title) < MIN_PAGE_LINK_TITLE_LENGTH:
            continue

        url = urljoin(page_url, href.strip())
        if not _same_origin(url, page_url):
            continue

        key = url or title.lower()
        if key in seen:
            continue
        seen.add(key)

        context = _nearby_context(html, match.start(), match.end())
        matched = keyword_matches(searchable_text(title, context, url), watch_keywords)
        ignored = keyword_matches(searchable_text(title, context, url), ignore_keywords)
        if ignored or (watch_keywords and not matched):
            continue

        published = _published_from_context(context)
        published_at = parse_datetime(published)
        updates.append(
            SourceUpdate(
                title=title,
                url=url,
                summary=context[:PAGE_LINK_CONTEXT_CHARS] if context is not None else None,
                published=published_at,
                published_at=published_at,
                matched_keywords=matched,
            )
        )

    return updates


async def resolve_page_image(source_url: str, fetch: FetchFn) -> str | None:
    return html_image_url(await fetch_provider_bytes(source_url, fetch, "Page"), source_url)
