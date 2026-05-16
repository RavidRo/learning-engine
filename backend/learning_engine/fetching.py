"""Network fetching primitives."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Mapping
from typing import cast
from urllib.parse import urlparse

from learning_engine.config import USER_AGENT

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


def _request_url(url: str, headers: Mapping[str, str]) -> bytes:
    if urlparse(url).scheme not in ALLOWED_URL_SCHEMES:
        msg = "Only HTTP and HTTPS URLs can be fetched"
        raise ValueError(msg)

    request_headers = {"User-Agent": USER_AGENT}
    request_headers.update(headers)

    request = urllib.request.Request(url, headers=request_headers)  # noqa: S310
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
        return cast(bytes, response.read())


def fetch_url(url: str) -> bytes:
    return _request_url(url, headers={})


def fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
    payload = json.loads(_request_url(url, headers=headers).decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Expected a JSON object response")
    return cast(dict[str, object], payload)
