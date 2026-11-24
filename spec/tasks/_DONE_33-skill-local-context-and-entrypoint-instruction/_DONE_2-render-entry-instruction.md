# Step 2: render_skill_md — инструкция entry point, без буллета navigation.yaml

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
`render_skill_md` рендерит инструкцию прочитать entry-файл адаптера и не вставляет буллет `spawn/navigation.yaml`.

## Approach
Изменить сигнатуру и тело `render_skill_md` в `src/spawn_cli/ide/_helpers.py`; передать имя entry-файла во всех 11 адаптерах.

## Affected files
- `src/spawn_cli/ide/_helpers.py` — `render_skill_md`, `_mandatory_reads_for_render`, `_NAV_YAML_FILE`, `_NAV_YAML_DESCRIPTION`.
- `src/spawn_cli/ide/claude_code.py` (строка 70), `cline.py` (59), `codex.py` (72), `cursor.py` (77), `gemini_cli.py` (84), `github_copilot.py` (95), `hermes.py` (60), `junie.py` (78), `mimo_code.py` (97), `opencode.py` (107), `windsurf.py` (53) — вызовы `render_skill_md`.

## Code changes (before / after)

### `src/spawn_cli/ide/_helpers.py` — `render_skill_md`, `_mandatory_reads_for_render`

**Before**
```python
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
```
Вставляет navigation.yaml последним буллетом Mandatory reads; без инструкции entry point.

**After**
```python
def render_skill_md(skill: SkillMetadata, entry_file: str | None = None) -> str:
    """Render normalized skill to Markdown with frontmatter, skill body,
    entrypoint instruction (when entry_file given), hints, mandatory reads,
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
    if entry_file:
        lines += [
            f"Before this skill, if the Spawn block instructions from "
            f"`{entry_file}` are not loaded, read `{entry_file}` first.",
            "",
        ]
    if skill.hints:
        lines += ["Hints:"]
        for h in skill.hints:
            lines += [f"- {h}"]
        lines += [""]
    lines += ["Mandatory reads:"]
    for ref in skill.required_read:
        lines += [f"- `{ref.file}` - {ref.description}"]
    lines += [""]
```
Инструкция entry point после body; Mandatory reads — как есть из метаданных, без вставки navigation.yaml. Удалить `_mandatory_reads_for_render`, `_NAV_YAML_FILE`, `_NAV_YAML_DESCRIPTION` и неиспользуемый импорт `_norm_read_path`/`SkillFileRef`, если они больше нигде в файле не используются.

### `src/spawn_cli/ide/*.py` — вызовы (примеры)

**Before**
```python
skill_path.write_text(render_skill_md(skill), encoding="utf-8")
```
**After**
```python
skill_path.write_text(render_skill_md(skill, "AGENTS.md"), encoding="utf-8")
```
Значения entry_file по адаптерам: cursor/codex/cline/windsurf/opencode/junie/mimo — `"AGENTS.md"`; claude_code — `"CLAUDE.md"`; gemini_cli — `"GEMINI.md"`; hermes — `".hermes.md"`; github_copilot — `".github/copilot-instructions.md"`.

Для адаптеров с `model_copy` (cline.py:59, hermes.py:60, junie.py:78, mimo_code.py:97, opencode.py:107): `render_skill_md(skill.model_copy(update={"name": name}), "AGENTS.md")` (hermes — `".hermes.md"`).

## Additional actions
- Проверить, что `_mandatory_reads_for_render` не используется в тестах/других модулях (`grep -rn _mandatory_reads_for_render src/ tests/`).
