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

# Dual-region agent ignore (core from spawn/.core vs extensions).
CORE_IGNORE_BLOCK_START = "# spawn:core:start"
CORE_IGNORE_BLOCK_END = "# spawn:core:end"
EXT_IGNORE_BLOCK_START = "# spawn:ext:start"
EXT_IGNORE_BLOCK_END = "# spawn:ext:end"

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


def _normalize_ignore_inner_lines(inner: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for ln in inner:
        st = ln.strip()
        if not st or st.startswith("#"):
            continue
        if st not in seen:
            seen.add(st)
            out.append(st)
    return out


def _format_optional_block(start: str, end: str, globs: list[str]) -> list[str]:
    body = [g for g in globs if g.strip()]
    if not body:
        return []
    lines = [start + "\n"] + [g.strip() + "\n" for g in body] + [end + "\n"]
    return lines


def _flatten_chunks(chunks: list[list[str]]) -> list[str]:
    out: list[str] = []
    for ch in chunks:
        out.extend(ch)
    return out


def _rebuild_from_user_chunks(
    chunks: list[list[str]], core_globs: list[str], ext_globs: list[str]
) -> list[str]:
    """Interleave user segments with core and ext blocks (see spawn agent-ignore spec)."""
    core_b = _format_optional_block(CORE_IGNORE_BLOCK_START, CORE_IGNORE_BLOCK_END, core_globs)
    ext_b = _format_optional_block(EXT_IGNORE_BLOCK_START, EXT_IGNORE_BLOCK_END, ext_globs)
    if not core_b and not ext_b:
        return _flatten_chunks(chunks)
    if len(chunks) == 0:
        return core_b + ext_b
    if len(chunks) == 1:
        return chunks[0] + core_b + ext_b
    if len(chunks) == 2:
        return chunks[0] + core_b + ext_b + chunks[1]
    out: list[str] = []
    out += chunks[0] + core_b + chunks[1] + ext_b
    for c in chunks[2:]:
        out += c
    return out


def _block_kind(line_stripped: str) -> str | None:
    if line_stripped == IGNORE_BLOCK_START:
        return "legacy"
    if line_stripped == CORE_IGNORE_BLOCK_START:
        return "core"
    if line_stripped == EXT_IGNORE_BLOCK_START:
        return "ext"
    return None


def _end_marker_for(kind: str) -> str:
    if kind == "legacy":
        return IGNORE_BLOCK_END
    if kind == "core":
        return CORE_IGNORE_BLOCK_END
    if kind == "ext":
        return EXT_IGNORE_BLOCK_END
    raise ValueError(kind)


def _parse_split_agent_ignore_lines(
    raw_lines: list[str],
) -> tuple[list[list[str]], list[str], list[str]]:
    """Split file into user chunks (between blocks), core globs, ext globs.

    Legacy ``# spawn:start`` … ``# spawn:end`` inner lines are discarded (migration).
    Unclosed blocks: inner runs to EOF.
    """
    chunks: list[list[str]] = []
    core: list[str] = []
    ext: list[str] = []
    cur: list[str] = []
    i = 0
    n = len(raw_lines)
    while i < n:
        kind = _block_kind(raw_lines[i].strip())
        if kind is None:
            cur.append(raw_lines[i])
            i += 1
            continue
        if cur:
            chunks.append(cur)
            cur = []
        end_marker = _end_marker_for(kind)
        j = i + 1
        inner: list[str] = []
        while j < n and raw_lines[j].strip() != end_marker:
            inner.append(raw_lines[j])
            j += 1
        if kind == "core":
            core = _normalize_ignore_inner_lines(inner)
        elif kind == "ext":
            ext = _normalize_ignore_inner_lines(inner)
        # legacy: discard inner
        i = j + 1 if j < n and raw_lines[j].strip() == end_marker else j
    if cur:
        chunks.append(cur)
    return chunks, core, ext


def parse_split_agent_ignore_file(file_path: Path) -> tuple[list[list[str]], list[str], list[str]]:
    if not file_path.exists():
        return [], [], []
    raw = file_path.read_text(encoding="utf-8").splitlines(True)
    return _parse_split_agent_ignore_lines(raw)


def write_split_agent_ignore_file(
    file_path: Path, chunks: list[list[str]], core_globs: list[str], ext_globs: list[str]
) -> None:
    body = _rebuild_from_user_chunks(chunks, core_globs, ext_globs)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not body:
        if file_path.exists():
            file_path.write_text("", encoding="utf-8")
        return
    file_path.write_text("".join(body), encoding="utf-8")


def rewrite_core_agent_ignore_region(file_path: Path, core_globs: list[str]) -> None:
    chunks, _, ext = parse_split_agent_ignore_file(file_path)
    write_split_agent_ignore_file(file_path, chunks, core_globs, ext)


def rewrite_extension_agent_ignore_region(file_path: Path, ext_globs: list[str]) -> None:
    chunks, core, _ = parse_split_agent_ignore_file(file_path)
    write_split_agent_ignore_file(file_path, chunks, core, ext_globs)


def clear_split_agent_ignore_file(file_path: Path) -> None:
    chunks, _, _ = parse_split_agent_ignore_file(file_path)
    write_split_agent_ignore_file(file_path, chunks, [], [])


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
    "CORE_IGNORE_BLOCK_END",
    "CORE_IGNORE_BLOCK_START",
    "EXT_IGNORE_BLOCK_END",
    "EXT_IGNORE_BLOCK_START",
    "IGNORE_BLOCK_END",
    "IGNORE_BLOCK_START",
    "SPAWN_BLOCK_END",
    "SPAWN_BLOCK_START",
    "clear_split_agent_ignore_file",
    "normalize_skill_name",
    "parse_split_agent_ignore_file",
    "remove_ignore_block",
    "render_skill_md",
    "rewrite_core_agent_ignore_region",
    "rewrite_extension_agent_ignore_region",
    "rewrite_ignore_block",
    "rewrite_managed_block",
    "write_split_agent_ignore_file",
]
