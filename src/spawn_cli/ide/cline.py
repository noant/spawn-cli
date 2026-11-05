"""Cline IDE adapter: .cline/skills, .clineignore, AGENTS.md; MCP unsupported."""

from __future__ import annotations

import warnings
from pathlib import Path

from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide._helpers import (
    clear_split_agent_ignore_file,
    remove_ignore_block,
    rewrite_core_agent_ignore_region,
    rewrite_extension_agent_ignore_region,
    rewrite_ignore_block,
    rewrite_managed_block,
)
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    register,
    normalize_skill_name,
    render_skill_md,
)
from spawn_cli.models.mcp import NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


class ClineAdapter(IdeAdapter):
    key = "cline"

    def detect(self, target_root: Path) -> DetectResult:
        used = (
            (target_root / ".cline").exists()
            or (target_root / ".clinerules").exists()
            or (target_root / ".clineignore").exists()
        )
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
            skill_dir = target_root / ".cline" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            # Cline requires frontmatter name == directory name.
            rendered = render_skill_md(skill.model_copy(update={"name": name}))
            skill_path.write_text(rendered, encoding="utf-8")
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
            "cline: Cline has no project-scope MCP settings; "
            "MCP is configured globally (cline_mcp_settings.json)"
        )
        return []

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        del target_root, rendered_mcp_names
        warnings.warn("cline: MCP is unsupported; nothing to remove")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".clineignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".clineignore", globs)

    def rewrite_core_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_core_agent_ignore_region(target_root / ".clineignore", globs)

    def rewrite_extension_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_extension_agent_ignore_region(target_root / ".clineignore", globs)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        clear_split_agent_ignore_file(target_root / ".clineignore")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_cline_repo(target_root)


register(ClineAdapter())

__all__ = ["ClineAdapter"]
