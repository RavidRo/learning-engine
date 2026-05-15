"""Technology source parsing and collection."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import urljoin, urlparse

from learning_engine.fetching import fetch_url
from learning_engine.models import (
    CollectionError,
    FeedUpdate,
    InterestsPayload,
    SourceType,
    TechnologyInterest,
    TechnologyUpdate,
    TechnologyUpdatesResponse,
)

FetchFn = Callable[[str], bytes]


def strip_markup(value: str) -> str:
    stripped = re.sub(r"<[^>]+>", "", unescape(value or ""))
    return re.sub(r"\s+", " ", stripped).strip()


def decode_html(page_bytes: bytes) -> str:
    return page_bytes.decode("utf-8", errors="replace")


def parse_datetime(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        parsed = None

    if parsed is None:
        for date_format in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(value, date_format).replace(tzinfo=UTC)
                break
            except ValueError:
                pass

    if parsed is None:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def days_cutoff(days: int | None, now: datetime | None = None) -> datetime | None:
    if days is None:
        return None
    reference = now or datetime.now(UTC)
    return reference.astimezone(UTC) - timedelta(days=days)


def within_window(published: str, cutoff: datetime | None) -> bool:
    if cutoff is None:
        return True
    parsed = parse_datetime(published)
    return parsed is not None and parsed >= cutoff


def child_text(element: ET.Element[str], names: tuple[str, ...]) -> str:
    for child in list(element):
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag in names:
            if tag == "link" and child.attrib.get("href"):
                return child.attrib["href"].strip()
            return "".join(child.itertext()).strip()
    return ""


def keyword_matches(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def parse_feed_items(
    feed_bytes: bytes,
    watch_keywords: list[str] | None = None,
    ignore_keywords: list[str] | None = None,
) -> list[FeedUpdate]:
    watch_keywords = watch_keywords or []
    ignore_keywords = ignore_keywords or []
    root = ET.fromstring(feed_bytes)
    items = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}]
    updates: list[FeedUpdate] = []

    for item in items:
        title = strip_markup(child_text(item, ("title",)))
        url = child_text(item, ("link",))
        summary = strip_markup(child_text(item, ("description", "summary", "content")))
        published = child_text(item, ("pubdate", "published", "updated"))
        searchable = " ".join([title, summary, url])
        matched = keyword_matches(searchable, watch_keywords)
        ignored = keyword_matches(searchable, ignore_keywords)
        if ignored or (watch_keywords and not matched):
            continue
        updates.append(
            FeedUpdate(
                title=title,
                url=url,
                summary=summary,
                published=published,
                published_at=format_datetime(parse_datetime(published)),
                matched_keywords=matched,
            )
        )

    return updates


def parse_page_items(
    page_bytes: bytes,
    page_url: str,
    watch_keywords: list[str] | None = None,
    ignore_keywords: list[str] | None = None,
) -> list[FeedUpdate]:
    """Best-effort official-page fallback for sites without RSS."""

    watch_keywords = watch_keywords or []
    ignore_keywords = ignore_keywords or []
    html = decode_html(page_bytes)
    link_pattern = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
    date_patterns = [
        re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
        re.compile(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}",
            re.IGNORECASE,
        ),
    ]
    updates: list[FeedUpdate] = []
    seen: set[str] = set()

    for match in link_pattern.finditer(html):
        href, body = match.groups()
        title = strip_markup(body)
        if len(title) < 8:
            continue

        url = urljoin(page_url, href.strip())
        parsed_url = urlparse(url)
        if parsed_url.netloc and parsed_url.netloc != urlparse(page_url).netloc:
            continue

        key = url or title.lower()
        if key in seen:
            continue
        seen.add(key)

        context = strip_markup(html[max(0, match.start() - 500) : match.end() + 500])
        searchable = " ".join([title, context, url])
        matched = keyword_matches(searchable, watch_keywords)
        ignored = keyword_matches(searchable, ignore_keywords)
        if ignored or (watch_keywords and not matched):
            continue

        published = ""
        for date_pattern in date_patterns:
            date_match = date_pattern.search(context)
            if date_match:
                published = date_match.group(0)
                break

        updates.append(
            FeedUpdate(
                title=title,
                url=url,
                summary=context[:500],
                published=published,
                published_at=format_datetime(parse_datetime(published)),
                matched_keywords=matched,
            )
        )

    return updates


def dedupe_updates(updates: list[TechnologyUpdate]) -> list[TechnologyUpdate]:
    deduped: list[TechnologyUpdate] = []
    seen: set[tuple[str, str]] = set()
    for update in updates:
        key = (update.url.strip(), update.title.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(update)
    return deduped


def _collect_from_interest(
    interest: TechnologyInterest,
    cutoff: datetime | None,
    fetch: FetchFn,
) -> tuple[list[TechnologyUpdate], CollectionError | None]:
    feed_url = interest.official_feed_url
    page_url = interest.official_site_url
    source_url = feed_url or page_url
    if not source_url:
        return [], None

    try:
        fetched = fetch(source_url)
        source_type: SourceType = "feed" if feed_url else "page"
        source_updates = (
            parse_feed_items(fetched, interest.watch_keywords, interest.ignore_keywords)
            if feed_url
            else parse_page_items(fetched, page_url, interest.watch_keywords, interest.ignore_keywords)
        )
    except Exception as exc:
        return [], CollectionError(interest_id=interest.id, interest_name=interest.name, error=str(exc))

    updates = [
        TechnologyUpdate(
            interest_id=interest.id,
            interest_name=interest.name,
            feed_url=feed_url,
            source_url=source_url,
            source_type=source_type,
            **source_update.model_dump(),
        )
        for source_update in source_updates
        if within_window(source_update.published_at or source_update.published, cutoff)
    ]
    return updates, None


def collect_technology_updates(
    payload: InterestsPayload,
    days: int | None = None,
    now: datetime | None = None,
    fetch: FetchFn = fetch_url,
) -> TechnologyUpdatesResponse:
    updates: list[TechnologyUpdate] = []
    errors: list[CollectionError] = []
    checked = 0
    cutoff = days_cutoff(days, now)

    for interest in payload.interests:
        if not interest.enabled:
            continue
        if not interest.official_feed_url and not interest.official_site_url:
            continue

        checked += 1
        source_updates, error = _collect_from_interest(interest, cutoff, fetch)
        updates.extend(source_updates)
        if error is not None:
            errors.append(error)

    updates = dedupe_updates(updates)
    updates.sort(key=lambda item: item.published_at or item.published or "", reverse=True)
    return TechnologyUpdatesResponse(
        interests_checked=checked,
        days=days,
        since=format_datetime(cutoff),
        updates=updates,
        errors=errors,
    )
