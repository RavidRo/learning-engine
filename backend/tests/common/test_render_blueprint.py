from pathlib import Path
from typing import Any, cast

from yaml import safe_load  # type: ignore[import-untyped]

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_render_backend_declares_mcp_allowed_hosts() -> None:
    blueprint = cast(dict[str, Any], safe_load((REPOSITORY_ROOT / "render.yaml").read_text()))
    services = cast(list[dict[str, Any]], blueprint["services"])
    backend = next(service for service in services if service["name"] == "learning-engine-backend")
    env_vars = cast(list[dict[str, str]], backend["envVars"])

    assert {"key": "MCP_ALLOWED_HOSTS", "value": "learning-engine-backend.onrender.com"} in env_vars
