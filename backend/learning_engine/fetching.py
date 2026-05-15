"""Network fetching primitives."""

from __future__ import annotations

import urllib.request
from typing import cast
from urllib.parse import urlparse

from learning_engine.config import USER_AGENT

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


def fetch_url(url: str) -> bytes:
    if urlparse(url).scheme not in ALLOWED_URL_SCHEMES:
        msg = "Only HTTP and HTTPS URLs can be fetched"
        raise ValueError(msg)

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
        return cast(bytes, response.read())
