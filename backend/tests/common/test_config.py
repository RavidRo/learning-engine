import pytest

from learning_engine import config


def test_clerk_issuer_returns_none_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLERK_ISSUER", raising=False)

    assert config.clerk_issuer() is None


def test_clerk_issuer_returns_none_when_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLERK_ISSUER", "  /  ")

    assert config.clerk_issuer() is None


def test_clerk_issuer_trims_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLERK_ISSUER", " https://example.clerk.accounts.dev/ ")

    assert config.clerk_issuer() == "https://example.clerk.accounts.dev"


def test_clerk_jwks_url_returns_none_without_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLERK_ISSUER", raising=False)
    monkeypatch.delenv("CLERK_JWKS_URL", raising=False)

    assert config.clerk_jwks_url() is None


def test_clerk_jwks_url_uses_explicit_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLERK_ISSUER", "https://example.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_JWKS_URL", " https://clerk.example.test/jwks.json ")

    assert config.clerk_jwks_url() == "https://clerk.example.test/jwks.json"


def test_clerk_jwks_url_returns_none_for_blank_explicit_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLERK_ISSUER", "https://example.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_JWKS_URL", "  ")

    assert config.clerk_jwks_url() is None


def test_clerk_jwks_url_uses_issuer_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLERK_ISSUER", "https://example.clerk.accounts.dev/")
    monkeypatch.delenv("CLERK_JWKS_URL", raising=False)

    assert config.clerk_jwks_url() == "https://example.clerk.accounts.dev/.well-known/jwks.json"


def test_clerk_authorized_parties_returns_empty_list_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLERK_AUTHORIZED_PARTIES", raising=False)

    assert config.clerk_authorized_parties() == []


def test_clerk_authorized_parties_parses_multiple_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", " http://localhost:5173,https://app.example.com , ")

    assert config.clerk_authorized_parties() == ["http://localhost:5173", "https://app.example.com"]


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


def test_mcp_allowed_hosts_returns_localhost_defaults_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)

    assert config.mcp_allowed_hosts() == ["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*"]


def test_mcp_allowed_hosts_extends_localhost_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", " learning-engine.example.com, api.example.com:443 , ")

    assert config.mcp_allowed_hosts() == [
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
        "learning-engine.example.com",
        "api.example.com:443",
    ]
