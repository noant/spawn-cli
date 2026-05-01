from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SkillFileRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file: str
    description: str


class SkillRawInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str
    content: str
    required_read: list[str] = Field(default_factory=list, alias="required-read")


class SkillMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str
    content: str
    hints: list[str] = Field(default_factory=list)
    required_read: list[SkillFileRef] = Field(default_factory=list)
    auto_read: list[SkillFileRef] = Field(default_factory=list)
