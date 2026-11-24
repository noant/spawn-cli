# Step 3: Обновление тестов

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Тесты `generate_skills_metadata` и `render_skill_md`/адаптеров отражают skill-local контент и инструкцию entry point.

## Approach
Обновить/удалить затронутые тесты в `tests/core/test_low_level.py`, `tests/ide/test_registry.py`, `tests/ide/test_cursor.py`; добавить тест инструкции entry point.

## Affected files
- `tests/core/test_low_level.py` — тесты на строках 104, 150, 196, 237, 291, 336, 386, 412.
- `tests/ide/test_registry.py` — `test_render_skill_md_minimal` (102), `test_render_skill_md_full` (122), `test_render_skill_md_mandatory_nav_reordered` (149), `test_render_skill_md_mandatory_nav_deduped` (169); новый тест.
- `tests/ide/test_cursor.py` — `test_add_skills_creates_file` (36-58).

## Code changes (before / after)

### `tests/core/test_low_level.py` — тесты metadata

**Before**
```
104: test_generate_skills_metadata — ожидает glob.md (global) в required, globs в auto
150: test_generate_skills_metadata_required_vs_contextual_dedup
196: test_generate_skills_metadata_required_paths_normalized_dedup
237: test_generate_skills_metadata_includes_navigation_rules_refs
291: test_generate_skills_metadata_hints_merge_and_contextual_ignored
336: test_generate_skills_metadata_global_hints_from_all_extensions
386: test_generate_skills_metadata_skill_hint_per_hint_truncate_warns (hints.global fixture)
412: test_generate_skills_metadata_combined_budget_adds_ellipsis_hint (hints.global fixture)
```

**After** (целевые ожидания)
- 104: `paths_two_set == {"extra.md"}` (glob.md — globalRead, исключён); auto пуст. Если нужно покрыть local-проброс — добавить в конфиг файл с `localRead: required`.
- 150: `req_paths == {"mixed-auto-local-required.md"}`; `auto_paths == {"mixed-global-required-local-auto.md", "ctx.md"}` — проверить по фактической фикстуре: остаются только local-категории.
- 196: required-ассерты (glob.md в required_read скилла) держатся; `auto_norm` становится пустым (ctx.md — globalRead:auto, исключён).
- 237: инвертировать — nav-rules refs НЕ входят в `required_read`/`auto_read` скилла (assert not in); переименовать в `test_generate_skills_metadata_excludes_navigation_rules_refs`.
- 291: hints скилла = только `hints.local` владельца; `hints.global` и maintainer-hints НЕ входят (assert not in).
- 336: глобальные hints НЕ входят в hints скилла; переименовать в `test_generate_skills_metadata_global_hints_excluded`.
- 386, 412: переключить фикстуры с `hints.global` на `hints.local` (бюджеты truncation/ellipsis по-прежнему проверяются на локальном пути); ассерты не меняются.

### `tests/ide/test_registry.py` — render-тесты

**Before**
```
102: test_render_skill_md_minimal — asserts nav bullet (117-118)
122: test_render_skill_md_full — asserts nav bullet + порядок (144, 146)
149: test_render_skill_md_mandatory_nav_reordered — весь тест про nav-last
169: test_render_skill_md_mandatory_nav_deduped — весь тест про nav dedup
189: test_render_skill_md_hints_before_mandatory_reads — выживает без изменений
```

**After**
- 102 (minimal): убрать nav-ассерты; добавить `assert "spawn/navigation.yaml" not in md`.
- 122 (full): убрать nav-ассерты/порядок; вызвать `render_skill_md(skill, "AGENTS.md")` и добавить `assert "read `AGENTS.md` first" in md`.
- 149, 169: удалить (спец-обработка nav в рендере устранена).
- Новый тест:

```python
def test_render_skill_md_entry_instruction() -> None:
    skill = SkillMetadata(
        name="s", description="d", content="body",
        required_read=[SkillFileRef(file="a.md", description="ad")],
        auto_read=[],
        hints=[],
    )
    md = render_skill_md(skill, "AGENTS.md")
    assert "read `AGENTS.md` first" in md
    assert "spawn/navigation.yaml" not in md
    md_no_entry = render_skill_md(skill)
    assert "AGENTS.md" not in md_no_entry
```

### `tests/ide/test_cursor.py` — `test_add_skills_creates_file`

**Before**
```python
    assert "- `spawn/navigation.yaml`" in text
    ... mand.index("spec/main.md") < mand.index("spawn/navigation.yaml") ...
```
Ассерты nav-буллета и порядка.

**After**
```python
    assert "read `AGENTS.md` first" in text
    assert "spawn/navigation.yaml" not in text
```
Навигация не рендерится в скилле; инструкция entry point присутствует. Nav-ассерты и проверку порядка удалить.

## Additional actions
- Прогнать: `pytest tests/core/test_low_level.py tests/ide/ -q`, затем весь сюит `pytest tests/ -q`.
