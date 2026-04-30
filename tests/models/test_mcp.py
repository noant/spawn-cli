from __future__ import annotations

import pytest
from pydantic import ValidationError

from spawn_cli.models.mcp import McpCapabilities, McpEnvVar, McpServer, McpTransport, NormalizedMcp


def test_mcp_transport_defaults() -> None:
    t = McpTransport.model_validate({"type": "stdio"})
    assert t.command is None
    assert t.args == []
    assert t.cwd == "."


def test_mcp_env_var_defaults() -> None:
    e = McpEnvVar.model_validate({})
    assert e.source == "user"
    assert e.required is True


def test_mcp_capabilities_defaults() -> None:
    c = McpCapabilities.model_validate({})
    assert c.tools is True
    assert c.resources is False


def test_mcp_server_minimal() -> None:
    s = McpServer.model_validate(
        {
            "name": "n",
            "extension": "e",
            "transport": {"type": "stdio", "command": "uvx"},
        }
    )
    assert s.name == "n"
    assert s.extension == "e"
    assert s.transport.command == "uvx"


def test_normalized_mcp_empty() -> None:
    m = NormalizedMcp.model_validate({})
    assert m.servers == []


def test_mcp_transport_missing_type() -> None:
    with pytest.raises(ValidationError):
        McpTransport.model_validate({})
