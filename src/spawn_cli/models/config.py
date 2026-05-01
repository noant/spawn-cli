from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FileMode(str, Enum):
    static = "static"
    artifact = "artifact"


class ReadFlag(str, Enum):
    required = "required"
    auto = "auto"
    no = "no"


class ExtensionFileEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: Optional[str] = None
    mode: FileMode = FileMode.static
    globalRead: ReadFlag = ReadFlag.no
    localRead: ReadFlag = ReadFlag.no


class ExtensionFolderEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: FileMode = FileMode.static


class SkillEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    required_read: list[str] = Field(default_factory=list, alias="required-read")


class ExtensionHints(BaseModel):
    """Optional extension-authored hints (plain strings only)."""

    model_config = ConfigDict(populate_by_name=True)

    global_: list[str] = Field(default_factory=list, alias="global")
    local: list[str] = Field(default_factory=list)


class SetupConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    before_install: Optional[str] = Field(None, alias="before-install")
    after_install: Optional[str] = Field(None, alias="after-install")
    before_uninstall: Optional[str] = Field(None, alias="before-uninstall")
    after_uninstall: Optional[str] = Field(None, alias="after-uninstall")
    healthcheck: Optional[str] = None


class ExtensionConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    version: str
    schema_version: int = Field(1, alias="schema")
    files: dict[str, ExtensionFileEntry] = Field(default_factory=dict)
    folders: dict[str, ExtensionFolderEntry] = Field(default_factory=dict)
    agent_ignore: list[str] = Field(default_factory=list, alias="agent-ignore")
    git_ignore: list[str] = Field(default_factory=list, alias="git-ignore")
    skills: dict[str, SkillEntry] = Field(default_factory=dict)
    setup: Optional[SetupConfig] = None
    hints: Optional[ExtensionHints] = None


class CoreConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    version: str
    agent_ignore: list[str] = Field(default_factory=list, alias="agent-ignore")


class IdeList(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ides: list[str] = Field(default_factory=list)


class SourceYaml(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class SourceInfo(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        type: str
        path: str
        branch: Optional[str] = None
        resolved: Optional[str] = None

    class InstalledInfo(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        version: str
        installedAt: str

    extension: str
    source: SourceInfo
    installed: InstalledInfo


class ExtensionsMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class ExtEntry(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        path: str
        branch: Optional[str] = None

    extensions: list[ExtEntry] = Field(default_factory=list)
