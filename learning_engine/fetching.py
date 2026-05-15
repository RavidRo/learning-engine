"""Network fetching primitives."""

from __future__ import annotations

import urllib.request
from typing import cast

from learning_engine.config import USER_AGENT


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        return cast(bytes, response.read())
