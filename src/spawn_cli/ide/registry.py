"""IDE adapter registry and abstract adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from spawn_cli.core.errors import SpawnError
from spawn_cli.core.low_level import CANONICAL_IDE_KEYS
from spawn_cli.ide._helpers import (
    IGNORE_BLOCK_END,
    IGNORE_BLOCK_START,
    SPAWN_BLOCK_END,
    SPAWN_BLOCK_START,
    normalize_skill_name,
    remove_ignore_block,
    render_skill_md,
    rewrite_ignore_block,
    rewrite_managed_block,
)
from spawn_cli.models.mcp import NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@dataclass
class IdeCapabilities:
    skills: str  # native | project | entry-only | external | unsupported
    mcp: str  # native | project | entry-only | external | unsupported
    agent_ignore: str  # native | project | entry-only | external | unsupported
    entry_point: str  # native | project | entry-only | external | unsupported

    def to_dict(self) -> dict:
        """Serialize to camelCase dict for YAML output."""
        return {
            "skills": self.skills,
            "mcp": self.mcp,
            "agentIgnore": self.agent_ignore,
            "entryPoint": self.entry_point,
        }


@dataclass
class DetectResult:
    used_in_repo: bool
    capabilities: IdeCapabilities


class IdeAdapter(ABC):
    key: str  # canonical key, defined on the class or instance

    @abstractmethod
    def detect(self, target_root: Path) -> DetectResult: ...

    @abstractmethod
    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        """Returns list of {skill: str, path: str} for ownership tracking."""
        ...

    @abstractmethod
    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None: ...

    @abstractmethod
    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        """Returns list of rendered server names."""
        ...

    @abstractmethod
    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None: ...

    @abstractmethod
    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None: ...

    @abstractmethod
    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None: ...

    @abstractmethod
    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        """Returns rendered path or warning string."""
        ...


ALIASES: dict[str, str] = {
    "claude": "claude-code",
    "qwen": "qwen-code",
    "gemini": "gemini-cli",
    "copilot": "github-copilot",
    "github": "github-copilot",
}

_registry: dict[str, IdeAdapter] = {}  # populated at module load by adapter modules


def register(adapter: IdeAdapter) -> None:
    """Register an adapter instance under its canonical key (must appear in CANONICAL_IDE_KEYS)."""
    key = getattr(adapter, "key", None)
    if key not in CANONICAL_IDE_KEYS:
        raise SpawnError(f"Cannot register unknown IDE key: {key!r}")
    _registry[key] = adapter


def get(name: str) -> IdeAdapter:
    """Resolve alias to canonical key to adapter. SpawnError on unknown."""
    canonical = ALIASES.get(name, name)
    if canonical not in _registry:
        raise SpawnError(f"Unknown IDE: {name!r}")
    return _registry[canonical]


def supported_ide_keys() -> list[str]:
    """Return the frozen ordered list from low_level (not dict iteration order)."""
    return list(CANONICAL_IDE_KEYS)


def detect_supported_ides(target_root: Path) -> dict[str, DetectResult]:
    """Run detect() for every canonical IDE key in CANONICAL_IDE_KEYS order."""
    return {key: get(key).detect(target_root) for key in CANONICAL_IDE_KEYS}


__all__ = [
    "ALIASES",
    "DetectResult",
    "IdeAdapter",
    "IdeCapabilities",
    "IGNORE_BLOCK_END",
    "IGNORE_BLOCK_START",
    "SPAWN_BLOCK_END",
    "SPAWN_BLOCK_START",
    "detect_supported_ides",
    "get",
    "normalize_skill_name",
    "register",
    "remove_ignore_block",
    "render_skill_md",
    "rewrite_ignore_block",
    "rewrite_managed_block",
    "supported_ide_keys",
]
