"""MCP presentation wiring for interest management tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from learning_engine.application import mcp_interest_commands as commands
from learning_engine.application.auth import UserContext
from learning_engine.application.ports import InterestRepository
from learning_engine.config import mcp_allowed_hosts, mcp_allowed_origins
from learning_engine.presentation.auth import (
    CLERK_AUTH_UNAVAILABLE_DETAIL,
    INVALID_AUTH_TOKEN_DETAIL,
    AuthConfigurationError,
    InvalidAuthTokenError,
    current_user_context,
    reset_current_user_context,
    set_current_user_context,
    user_context_from_authorization,
)

MCP_ORIGIN_FORBIDDEN_DETAIL = "MCP browser origin is not allowed"


class AuthenticatedMcpApp:
    def __init__(self, api: FastAPI, app: ASGIApp) -> None:
        self._api = api
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = _headers(scope)
        origin = headers.get("origin")
        if origin is not None and origin not in mcp_allowed_origins():
            await _json_response(MCP_ORIGIN_FORBIDDEN_DETAIL, 403, scope, receive, send)
            return

        try:
            user_context = user_context_from_authorization(self._api, headers.get("authorization"))
        except AuthConfigurationError:
            await _json_response(CLERK_AUTH_UNAVAILABLE_DETAIL, 503, scope, receive, send)
            return
        except InvalidAuthTokenError:
            await _json_response(INVALID_AUTH_TOKEN_DETAIL, 401, scope, receive, send)
            return

        token = set_current_user_context(user_context)
        try:
            await self._app(scope, receive, send)
        finally:
            reset_current_user_context(token)


def create_interest_mcp_server(api: FastAPI) -> FastMCP:  # noqa: C901
    mcp = FastMCP(
        "Signal Garden Interest Management",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
        transport_security=TransportSecuritySettings(
            allowed_hosts=mcp_allowed_hosts(),
            allowed_origins=mcp_allowed_origins(),
        ),
    )

    @mcp.tool()
    def list_interests(include_deleted: bool = False) -> commands.CommandResponse:
        """List interests and sources, excluding soft-deleted records unless requested."""
        return _tool_result(
            lambda: commands.list_interests(
                _interest_repository(api),
                _user_context(),
                include_deleted=include_deleted,
            )
        )

    @mcp.tool()
    def create_interest(command: commands.InterestCreateInput) -> commands.CommandResponse:
        """Create an interest with server-generated IDs for the interest and sources."""
        return _tool_result(lambda: commands.create_interest(_interest_repository(api), _user_context(), command))

    @mcp.tool()
    def update_interest(interest_id: str, command: commands.InterestUpdateInput) -> commands.CommandResponse:
        """Update fields for an existing non-deleted interest by ID."""
        return _tool_result(
            lambda: commands.update_interest(_interest_repository(api), _user_context(), interest_id, command)
        )

    @mcp.tool()
    def pause_interest(interest_id: str) -> commands.CommandResponse:
        """Pause an interest by setting enabled to false."""
        return _tool_result(lambda: commands.pause_interest(_interest_repository(api), _user_context(), interest_id))

    @mcp.tool()
    def resume_interest(interest_id: str) -> commands.CommandResponse:
        """Resume an interest by setting enabled to true."""
        return _tool_result(lambda: commands.resume_interest(_interest_repository(api), _user_context(), interest_id))

    @mcp.tool()
    def delete_interest(interest_id: str) -> commands.CommandResponse:
        """Soft-delete an interest by ID."""
        return _tool_result(lambda: commands.delete_interest(_interest_repository(api), _user_context(), interest_id))

    @mcp.tool()
    def add_source(interest_id: str, command: commands.SourceInput) -> commands.CommandResponse:
        """Add a source to an existing non-deleted interest with a server-generated source ID."""
        return _tool_result(
            lambda: commands.add_source(_interest_repository(api), _user_context(), interest_id, command)
        )

    @mcp.tool()
    def update_source(
        interest_id: str,
        source_id: str,
        command: commands.SourceUpdateInput,
    ) -> commands.CommandResponse:
        """Update fields for an existing non-deleted source by interest ID and source ID."""
        return _tool_result(
            lambda: commands.update_source(_interest_repository(api), _user_context(), interest_id, source_id, command)
        )

    @mcp.tool()
    def pause_source(interest_id: str, source_id: str) -> commands.CommandResponse:
        """Pause a source by setting enabled to false."""
        return _tool_result(
            lambda: commands.pause_source(_interest_repository(api), _user_context(), interest_id, source_id)
        )

    @mcp.tool()
    def resume_source(interest_id: str, source_id: str) -> commands.CommandResponse:
        """Resume a source by setting enabled to true."""
        return _tool_result(
            lambda: commands.resume_source(_interest_repository(api), _user_context(), interest_id, source_id)
        )

    @mcp.tool()
    def delete_source(interest_id: str, source_id: str) -> commands.CommandResponse:
        """Soft-delete a source by interest ID and source ID."""
        return _tool_result(
            lambda: commands.delete_source(_interest_repository(api), _user_context(), interest_id, source_id)
        )

    return mcp


def create_authenticated_mcp_app(api: FastAPI, mcp: FastMCP) -> ASGIApp:
    return AuthenticatedMcpApp(api, mcp.streamable_http_app())


def _interest_repository(api: FastAPI) -> InterestRepository:
    return cast(InterestRepository, api.state.interest_repository)


def _user_context() -> UserContext:
    return current_user_context()


def _tool_result(action: Callable[[], commands.CommandResponse]) -> commands.CommandResponse:
    try:
        return action()
    except commands.McpInterestCommandError as exc:
        raise ToolError(str(exc)) from exc


def _headers(scope: Scope) -> dict[str, str]:
    return {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope["headers"]}


async def _json_response(
    detail: str,
    status_code: int,
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    response = JSONResponse({"detail": detail}, status_code=status_code)
    typed_response = response
    await typed_response(scope, receive, send)
