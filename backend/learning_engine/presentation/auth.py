"""Authentication boundary for protected FastAPI and MCP requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextvars import ContextVar, Token
from typing import Any, Protocol, cast

import jwt
from fastapi import FastAPI, Header, HTTPException, status
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError

from learning_engine.application.auth import UserContext
from learning_engine.config import clerk_authorized_parties, clerk_issuer, clerk_jwks_url

CLERK_AUTH_UNAVAILABLE_DETAIL = "Authentication is unavailable because Clerk is not configured"
INVALID_AUTH_TOKEN_DETAIL = "Missing or invalid Clerk bearer token"  # noqa: S105
_CURRENT_USER_CONTEXT: ContextVar[UserContext | None] = ContextVar("current_user_context", default=None)


class AuthenticationError(Exception):
    """Raised when a request cannot be authenticated."""


class AuthConfigurationError(AuthenticationError):
    """Raised when authentication cannot run because configuration is missing."""


class InvalidAuthTokenError(AuthenticationError):
    """Raised when request credentials are missing or invalid."""


class SigningKey(Protocol):
    key: Any


class SigningKeyClient(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> SigningKey: ...


class ClerkTokenVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        jwks_client: SigningKeyClient,
        authorized_parties: Sequence[str],
    ) -> None:
        self._issuer = issuer
        self._jwks_client = jwks_client
        self._authorized_parties = set(authorized_parties)

    @classmethod
    def from_config(cls) -> "ClerkTokenVerifier":
        issuer = clerk_issuer()
        jwks_url = clerk_jwks_url()
        if issuer is None or jwks_url is None:
            raise AuthConfigurationError(CLERK_AUTH_UNAVAILABLE_DETAIL)
        return cls(
            issuer=issuer,
            jwks_client=PyJWKClient(jwks_url),
            authorized_parties=clerk_authorized_parties(),
        )

    def verify_token(self, token: str) -> UserContext:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = cast(
                Mapping[str, Any],
                jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256"],
                    issuer=self._issuer,
                    options={"require": ["exp", "sub"]},
                ),
            )
        except (InvalidTokenError, PyJWKClientError) as exc:
            raise InvalidAuthTokenError(INVALID_AUTH_TOKEN_DETAIL) from exc

        self._raise_on_unauthorized_party(claims)
        user_id = claims["sub"]
        if not isinstance(user_id, str) or user_id.strip() == "":
            raise InvalidAuthTokenError(INVALID_AUTH_TOKEN_DETAIL)
        return UserContext(user_id=user_id)

    def _raise_on_unauthorized_party(self, claims: Mapping[str, Any]) -> None:
        if not self._authorized_parties:
            return
        authorized_party = claims.get("azp")
        if not isinstance(authorized_party, str) or authorized_party not in self._authorized_parties:
            raise InvalidAuthTokenError(INVALID_AUTH_TOKEN_DETAIL)


def bearer_token_from_authorization(authorization: str | None) -> str:
    if authorization is None:
        raise InvalidAuthTokenError(INVALID_AUTH_TOKEN_DETAIL)
    scheme, separator, token = authorization.partition(" ")
    if separator == "" or scheme.lower() != "bearer" or token.strip() == "":
        raise InvalidAuthTokenError(INVALID_AUTH_TOKEN_DETAIL)
    return token.strip()


def user_context_dependency(api: FastAPI) -> Callable[[str | None], UserContext]:
    def require_user_context(authorization: str | None = Header(default=None)) -> UserContext:
        try:
            return user_context_from_authorization(api, authorization)
        except AuthConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=CLERK_AUTH_UNAVAILABLE_DETAIL,
            ) from exc
        except InvalidAuthTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_AUTH_TOKEN_DETAIL) from exc

    return require_user_context


def user_context_from_authorization(api: FastAPI, authorization: str | None) -> UserContext:
    return _token_verifier(api).verify_token(bearer_token_from_authorization(authorization))


def set_current_user_context(user_context: UserContext) -> Token[UserContext | None]:
    return _CURRENT_USER_CONTEXT.set(user_context)


def reset_current_user_context(token: Token[UserContext | None]) -> None:
    _CURRENT_USER_CONTEXT.reset(token)


def current_user_context() -> UserContext:
    user_context = _CURRENT_USER_CONTEXT.get()
    if user_context is None:
        raise InvalidAuthTokenError(INVALID_AUTH_TOKEN_DETAIL)
    return user_context


def _token_verifier(api: FastAPI) -> ClerkTokenVerifier:
    configured_verifier = getattr(api.state, "auth_verifier", None)
    if configured_verifier is not None:
        return cast(ClerkTokenVerifier, configured_verifier)
    verifier = ClerkTokenVerifier.from_config()
    api.state.auth_verifier = verifier
    return verifier
