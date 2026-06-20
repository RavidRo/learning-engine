from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from learning_engine.presentation.auth import (
    AuthConfigurationError,
    ClerkTokenVerifier,
    InvalidAuthTokenError,
    bearer_token_from_authorization,
)


class StaticSigningKey:
    def __init__(self, key: RSAPublicKey) -> None:
        self.key = key


class StaticSigningKeyClient:
    def __init__(self, key: RSAPublicKey) -> None:
        self.key = key

    def get_signing_key_from_jwt(self, _token: str) -> StaticSigningKey:
        return StaticSigningKey(self.key)


def test_bearer_token_from_authorization_extracts_token() -> None:
    assert bearer_token_from_authorization("Bearer token-value") == "token-value"


@pytest.mark.parametrize(
    "authorization",
    [
        None,
        "",
        "token-value",
        "Basic token-value",
        "Bearer  ",
    ],
)
def test_bearer_token_from_authorization_rejects_missing_or_invalid_token(authorization: str | None) -> None:
    with pytest.raises(InvalidAuthTokenError):
        bearer_token_from_authorization(authorization)


def test_clerk_token_verifier_from_config_requires_clerk_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLERK_ISSUER", raising=False)
    monkeypatch.delenv("CLERK_JWKS_URL", raising=False)

    with pytest.raises(AuthConfigurationError):
        ClerkTokenVerifier.from_config()


def test_clerk_token_verifier_returns_user_context_for_valid_token() -> None:
    private_key = _private_key()
    verifier = _verifier(public_key=private_key.public_key())

    context = verifier.verify_token(_token(private_key, {"sub": "user_123"}))

    assert context.user_id == "user_123"


def test_clerk_token_verifier_rejects_invalid_token() -> None:
    verifier = _verifier(public_key=_private_key().public_key())

    with pytest.raises(InvalidAuthTokenError):
        verifier.verify_token("not-a-jwt")


def test_clerk_token_verifier_rejects_expired_token() -> None:
    private_key = _private_key()
    verifier = _verifier(public_key=private_key.public_key())

    token = _token(private_key, {"sub": "user_123", "exp": datetime.now(UTC) - timedelta(minutes=1)})

    with pytest.raises(InvalidAuthTokenError):
        verifier.verify_token(token)


def test_clerk_token_verifier_rejects_wrong_issuer() -> None:
    private_key = _private_key()
    verifier = _verifier(public_key=private_key.public_key())

    token = _token(private_key, {"sub": "user_123", "iss": "https://wrong.example.com"})

    with pytest.raises(InvalidAuthTokenError):
        verifier.verify_token(token)


def test_clerk_token_verifier_rejects_unauthorized_party() -> None:
    private_key = _private_key()
    verifier = _verifier(
        public_key=private_key.public_key(),
        authorized_parties=["https://app.example.com"],
    )

    token = _token(private_key, {"sub": "user_123", "azp": "https://other.example.com"})

    with pytest.raises(InvalidAuthTokenError):
        verifier.verify_token(token)


def _private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _verifier(
    *,
    public_key: RSAPublicKey,
    authorized_parties: list[str] | None = None,
) -> ClerkTokenVerifier:
    return ClerkTokenVerifier(
        issuer="https://clerk.example.com",
        jwks_client=StaticSigningKeyClient(public_key),
        authorized_parties=authorized_parties or [],
    )


def _token(private_key: RSAPrivateKey, overrides: dict[str, Any]) -> str:
    claims: dict[str, Any] = {
        "iss": "https://clerk.example.com",
        "sub": "user_123",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")
