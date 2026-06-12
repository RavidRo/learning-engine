import pytest

from learning_engine import config


def test_mcp_auth_token_returns_none_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)

    assert config.mcp_auth_token() is None


def test_mcp_auth_token_returns_none_when_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", " \t ")

    assert config.mcp_auth_token() is None


def test_mcp_auth_token_trims_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", " secret-token \n")

    assert config.mcp_auth_token() == "secret-token"


def test_mcp_allowed_origins_returns_empty_list_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_ALLOWED_ORIGINS", raising=False)

    assert config.mcp_allowed_origins() == []


def test_mcp_allowed_origins_returns_empty_list_for_blank_items(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_ALLOWED_ORIGINS", " ,  ,, ")

    assert config.mcp_allowed_origins() == []


def test_mcp_allowed_origins_parses_multiple_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "MCP_ALLOWED_ORIGINS",
        " https://app.example.com,https://agent.example.com , ",
    )

    assert config.mcp_allowed_origins() == ["https://app.example.com", "https://agent.example.com"]
