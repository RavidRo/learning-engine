from __future__ import annotations

from learning_engine.infrastructure.source_collectors.spotify import spotify_show_id
from learning_engine.infrastructure.source_collectors.twitter import twitter_username


def test_twitter_username_accepts_common_forms() -> None:
    assert twitter_username("https://twitter.com/openai") == "openai"
    assert twitter_username("@openai") == "openai"


def test_spotify_show_id_accepts_common_forms() -> None:
    assert spotify_show_id("spotify:show:show-id") == "show-id"
    assert spotify_show_id("https://open.spotify.com/show/show-id?si=abc") == "show-id"
