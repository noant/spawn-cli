"""Windsurf IDE adapter: .windsurf/skills, .codeiumignore, AGENTS.md; MCP unsupported."""

from __future__ import annotations

import warnings
from pathlib import Path

from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    register,
    normalize_skill_name,
    render_skill_md,
    rewrite_managed_block,
    rewrite_ignore_block,
    remove_ignore_block,
)
from spawn_cli.models.mcp import NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


class WindsurfAdapter(IdeAdapter):
    key = "windsurf"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".windsurf").exists() or (target_root / ".codeiumignore").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="unsupported",
                agent_ignore="native",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".windsurf" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            skill_path.write_text(render_skill_md(skill), encoding="utf-8")
            rel = skill_path.relative_to(target_root).as_posix()
            results.append({"skill": skill.name, "path": rel})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        del normalized_mcp
        del target_root
        warnings.warn(
            "windsurf: Windsurf does not support project MCP config; "
            "MCP is configured globally in Cascade"
        )
        return []

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        del target_root, rendered_mcp_names
        warnings.warn("windsurf: MCP is unsupported; nothing to remove")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".codeiumignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".codeiumignore", globs)

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_standard_dotdir_skills_and_mcp(target_root, ".windsurf", allow_delete_entire=True)


register(WindsurfAdapter())

__all__ = ["WindsurfAdapter"]
