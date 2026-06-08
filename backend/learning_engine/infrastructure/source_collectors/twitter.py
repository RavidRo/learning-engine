"""X/Twitter account collection through the official X API."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast
from urllib.parse import quote, urlparse

from learning_engine.common.dates import parse_datetime
from learning_engine.config import X_API_ORIGIN, twitter_bearer_token
from learning_engine.domain.updates import SourceUpdate

JsonFetchFn = Callable[[str, Mapping[str, str]], Awaitable[dict[str, object]]]


def twitter_username(source_url: str) -> str:
    stripped = source_url.strip()
    if not stripped:
        raise ValueError("Twitter account source URL is required")

    parsed = urlparse(stripped)
    if parsed.netloc:
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return parts[0].removeprefix("@")

    return stripped.removeprefix("@")


def _headers() -> Mapping[str, str]:
    token = twitter_bearer_token()
    if token is None:
        raise ValueError("Twitter bearer token is required for twitter_account sources")
    return {"Authorization": f"Bearer {token}"}


def _user_id(response: Mapping[str, object]) -> str:
    data = response.get("data")
    if not isinstance(data, dict):
        raise TypeError("Twitter user lookup response did not include user data")

    user_id = data.get("id")
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("Twitter user lookup response did not include a user id")
    return user_id


def _tweet_url(username: str, tweet_id: object) -> str | None:
    if not isinstance(tweet_id, str) or not tweet_id.strip():
        return None
    return f"https://x.com/{username}/status/{tweet_id}"


def _tweet_update(username: str, tweet: Mapping[str, object]) -> SourceUpdate:
    text = str(tweet.get("text") or "").strip()
    created_at = str(tweet.get("created_at") or "").strip() or None
    published_at = parse_datetime(created_at)
    return SourceUpdate(
        title=text[:120] or None,
        url=_tweet_url(username, tweet.get("id")),
        summary=text or None,
        published=published_at,
        published_at=published_at,
    )


async def collect_twitter_account(source_url: str, fetch_json: JsonFetchFn) -> list[SourceUpdate]:
    username = twitter_username(source_url)
    headers = _headers()
    user = await fetch_json(f"{X_API_ORIGIN}/users/by/username/{quote(username)}", headers)
    user_id = _user_id(user)
    timeline = await fetch_json(
        f"{X_API_ORIGIN}/users/{quote(user_id)}/tweets?max_results=20&tweet.fields=created_at&exclude=retweets,replies",
        headers,
    )
    tweets = timeline.get("data", [])
    if not isinstance(tweets, list):
        return []

    return [_tweet_update(username, cast(Mapping[str, Any], tweet)) for tweet in tweets if isinstance(tweet, dict)]
