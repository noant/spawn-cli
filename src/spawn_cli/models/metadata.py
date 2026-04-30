from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RenderedSkillEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    skill: str
    path: str


class RenderedSkillsMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    extensions: dict[str, list[RenderedSkillEntry]] = Field(default_factory=dict)


class RenderedMcpEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str


class RenderedMcpMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    extensions: dict[str, list[RenderedMcpEntry]] = Field(default_factory=dict)
