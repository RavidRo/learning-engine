"""Date parsing and recency-window helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except TypeError, ValueError:
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


def format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def days_cutoff(days: int | None, now: datetime) -> datetime | None:
    if days is None:
        return None
    return now.astimezone(UTC) - timedelta(days=days)


def within_window(published: str | None, cutoff: datetime | None) -> bool:
    if cutoff is None:
        return True
    parsed = parse_datetime(published)
    return parsed is not None and parsed >= cutoff
