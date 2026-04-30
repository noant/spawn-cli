from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class McpEnvVar(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str = "user"
    required: bool = True
    secret: bool = False
    value: Optional[str] = None


class McpCapabilities(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tools: bool = True
    resources: bool = False
    prompts: bool = False


class McpTransport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    command: Optional[str] = None
    args: list[str] = Field(default_factory=list)
    cwd: str = "."
    url: Optional[str] = None
    headers: dict[str, str] = Field(default_factory=dict)


class McpServer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    extension: str
    transport: McpTransport
    env: dict[str, McpEnvVar] = Field(default_factory=dict)
    capabilities: McpCapabilities = Field(default_factory=McpCapabilities)


class NormalizedMcp(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    servers: list[McpServer] = Field(default_factory=list)
