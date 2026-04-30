from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NavFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    path: str
    description: str


class NavExtGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ext: str
    files: list[NavFile] = Field(default_factory=list)


class NavRulesGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rules: list[NavFile] = Field(default_factory=list)


class NavigationFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    read_required: list[dict] = Field(default_factory=list, alias="read-required")
    read_contextual: list[dict] = Field(default_factory=list, alias="read-contextual")
