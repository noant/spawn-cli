from __future__ import annotations

import warnings
from pathlib import Path

from .registry import DetectResult, IdeAdapter, IdeCapabilities
from spawn_cli.models.mcp import NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


class StubAdapter(IdeAdapter):
    def __init__(self, key: str, caps: IdeCapabilities) -> None:
        self.key = key
        self._caps = caps

    def detect(self, target_root: Path) -> DetectResult:
        del target_root
        return DetectResult(used_in_repo=False, capabilities=self._caps)

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        del target_root, skill_metadata
        warnings.warn(f"{self.key}: skill rendering not yet implemented")
        return []

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        del target_root, rendered_paths
        warnings.warn(f"{self.key}: skill removal not yet implemented")

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        del target_root, normalized_mcp
        warnings.warn(f"{self.key}: MCP rendering not yet implemented")
        return []

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        del target_root, rendered_mcp_names
        warnings.warn(f"{self.key}: MCP removal not yet implemented")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn(f"{self.key}: agent ignore not yet implemented")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn(f"{self.key}: agent ignore removal not yet implemented")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        del target_root, prompt
        warnings.warn(f"{self.key}: entry point not yet implemented")
        return ""


__all__ = ["StubAdapter"]
