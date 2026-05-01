"""Shared IDE adapter rendering helpers."""

from __future__ import annotations

import re
from pathlib import Path

from spawn_cli.core.low_level import _norm_read_path, normalize_skill_name
from spawn_cli.models.skill import SkillFileRef, SkillMetadata

SPAWN_BLOCK_START = "<!-- spawn:start -->"
SPAWN_BLOCK_END = "<!-- spawn:end -->"

IGNORE_BLOCK_START = "# spawn:start"
IGNORE_BLOCK_END = "# spawn:end"

_NAV_YAML_FILE = "spawn/navigation.yaml"
_NAV_YAML_DESCRIPTION = "Merged Spawn navigation (read-required, read-contextual)."


def _mandatory_reads_for_render(skill: SkillMetadata) -> list[SkillFileRef]:
    """Build mandatory list with spawn/navigation.yaml deduped and last."""
    nav_key = _norm_read_path(_NAV_YAML_FILE)
    nav_ref: SkillFileRef | None = None
    others: list[SkillFileRef] = []
    for ref in skill.required_read:
        if _norm_read_path(ref.file) == nav_key:
            if nav_ref is None:
                nav_ref = ref
        else:
            others.append(ref)
    if nav_ref is None:
        nav_ref = SkillFileRef(file=_NAV_YAML_FILE, description=_NAV_YAML_DESCRIPTION)
    return others + [nav_ref]


def render_skill_md(skill: SkillMetadata) -> str:
    """Render normalized skill to Markdown with frontmatter, skill body,
    hints (stable order from metadata), mandatory reads (navigation path last),
    and contextual reads."""
    lines = [
        "---",
        f"name: {skill.name}",
        f"description: {skill.description}",
        "---",
        "",
        skill.content,
        "",
    ]
    if skill.hints:
        lines += ["Hints:"]
        for h in skill.hints:
            lines += [f"- {h}"]
        lines += [""]
    lines += ["Mandatory reads:"]
    for ref in _mandatory_reads_for_render(skill):
        lines += [f"- `{ref.file}` - {ref.description}"]
    lines += [""]
    if skill.auto_read:
        lines += ["Contextual reads:"]
        for ref in skill.auto_read:
            lines += [f"- `{ref.file}` - {ref.description}"]
        lines += [""]
    return "\n".join(lines)


def rewrite_managed_block(file_path: Path, prompt: str) -> None:
    """Read file (or empty string), replace/insert spawn block, write back."""
    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    block = f"{SPAWN_BLOCK_START}\n{prompt}\n{SPAWN_BLOCK_END}"
    if SPAWN_BLOCK_START in content:
        content = re.sub(
            rf"{re.escape(SPAWN_BLOCK_START)}.*?{re.escape(SPAWN_BLOCK_END)}",
            block,
            content,
            flags=re.DOTALL,
        )
    else:
        content = block + "\n" + content
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def _partition_ignore_block(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    start_idx: int | None = None
    end_idx: int | None = None
    for i, ln in enumerate(lines):
        if ln.strip() == IGNORE_BLOCK_START:
            start_idx = i
            break
    if start_idx is None:
        return lines[:], [], []
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip() == IGNORE_BLOCK_END:
            end_idx = j
            break
    if end_idx is None:
        return lines[:start_idx], lines[start_idx + 1 :], []
    return lines[:start_idx], lines[start_idx + 1 : end_idx], lines[end_idx + 1 :]


def rewrite_ignore_block(file_path: Path, globs: list[str]) -> None:
    """Merge Spawn-owned globs into a text ignore file using # spawn:start / # spawn:end."""
    raw_lines = (
        file_path.read_text(encoding="utf-8").splitlines(True)
        if file_path.exists()
        else []
    )
    before, _inner, after = _partition_ignore_block(raw_lines)
    body_lines = [g.strip() + "\n" for g in globs if g.strip()]
    block_lines = (
        [IGNORE_BLOCK_START + "\n"]
        + body_lines
        + [IGNORE_BLOCK_END + "\n"]
    )
    new_lines = before + block_lines + after
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("".join(new_lines), encoding="utf-8")


def remove_ignore_block(file_path: Path, globs: list[str]) -> None:
    """Remove Spawn-managed ignore lines or the whole managed block.

    If ``globs`` is empty, removes the entire ``# spawn:start`` … ``# spawn:end`` block.
    If ``globs`` is non-empty, removes only inner lines whose stripped text matches
    an entry in ``globs``; preserves other inner lines and all content outside the block.
    If no inner lines remain, the block markers are removed as well.
    """
    if not file_path.exists():
        return
    raw_lines = file_path.read_text(encoding="utf-8").splitlines(True)
    start_idx: int | None = None
    end_idx: int | None = None
    for i, ln in enumerate(raw_lines):
        if ln.strip() == IGNORE_BLOCK_START:
            start_idx = i
            break
    if start_idx is None:
        return
    for j in range(start_idx + 1, len(raw_lines)):
        if raw_lines[j].strip() == IGNORE_BLOCK_END:
            end_idx = j
            break
    if end_idx is None:
        return

    before = raw_lines[:start_idx]
    inner = raw_lines[start_idx + 1 : end_idx]
    after = raw_lines[end_idx + 1 :]

    if not globs:
        file_path.write_text("".join(before + after), encoding="utf-8")
        return

    drop = {g.strip() for g in globs if g.strip()}
    kept = [ln for ln in inner if ln.strip() not in drop]
    if not kept:
        file_path.write_text("".join(before + after), encoding="utf-8")
    else:
        block_lines = [IGNORE_BLOCK_START + "\n"] + kept + [IGNORE_BLOCK_END + "\n"]
        file_path.write_text("".join(before + block_lines + after), encoding="utf-8")


__all__ = [
    "IGNORE_BLOCK_END",
    "IGNORE_BLOCK_START",
    "SPAWN_BLOCK_END",
    "SPAWN_BLOCK_START",
    "normalize_skill_name",
    "remove_ignore_block",
    "render_skill_md",
    "rewrite_ignore_block",
    "rewrite_managed_block",
]
