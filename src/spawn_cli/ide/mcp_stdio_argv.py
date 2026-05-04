"""Shared argv list for IDE MCP configs that launch ``spawn mcp_stdio``."""

from __future__ import annotations


def mcp_stdio_argv(extension_id: str, server_name: str) -> list[str]:
    return ["mcp_stdio", "extension", extension_id, "name", server_name]


__all__ = ["mcp_stdio_argv"]
