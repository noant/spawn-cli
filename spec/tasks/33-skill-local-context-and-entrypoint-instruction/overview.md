# 33: Скиллы содержат только локальный контекст + инструкция прочитать entry point

## Source seed
- Path: none

## Status
- [V] Research [glm-5.3]
- [ ] User research review
- [V] Spec drafting [glm-5.3]
- [V] Spec self-review [deepseek-v4-pro + glm-5.3]
- [ ] Spec review
- [V] Code implementation [glm-5.3]
- [V] Code self-review [deepseek-v4-pro + glm-5.3]
- [ ] Code review / debugging
- [V] Design document update [glm-5.3]

## Goal
В рендере скиллов оставить только skill-specific контекст (skill `required-read`, `localRead` владельца, `hints.local`), глобальные риды/hints и navigation-дубли убрать — вместо них одна инструкция прочитать entry point файл, если его инструкции ещё не загружены.

## Motivation
После задачи 32 entry-блок (AGENTS.md / CLAUDE.md / GEMINI.md / .hermes.md / .github/copilot-instructions.md) уже несёт целиком `spawn/navigation.yaml` + rollup hints. Глобальные риды и hints в каждом скилле теперь чистое дублирование. Решено: без исключений по IDE, единый формат для всех адаптеров.

## Invasiveness level
medium-invasive

## Review models
- Research review: single agent: glm-5.3-flash
- Spec review: cross-review: deepseek-v4-pro, glm-5.3
- Code review: cross-review: deepseek-v4-pro, glm-5.3

## Run mode
auto

## Research summary
- `generate_skills_metadata` (`src/spawn_cli/core/low_level.py`, строки 546-632): сейчас в required каждого скилла мержит `raw.required_read + local_required + merged_global_required + nav_rules_required`; в auto — `local_auto + merged_global_auto + nav_rules_contextual`; hints — `global_streams + local + maintainer_hints`.
- `render_skill_md` + `_mandatory_reads_for_render` (`src/spawn_cli/ide/_helpers.py`, строки 23-70): вставляет буллет `spawn/navigation.yaml` последним в Mandatory reads; рендер: frontmatter, body, Hints, Mandatory reads, Contextual reads.
- Вызовы `render_skill_md(skill)` в 11 адаптерах (claude_code.py:70, cline.py:59, codex.py:72, cursor.py:77, gemini_cli.py:84, github_copilot.py:95, hermes.py:60, junie.py:78, mimo_code.py:97, opencode.py:107, windsurf.py:53).
- Entry-файлы адаптеров: AGENTS.md (cursor, codex, cline, windsurf, opencode, junie, mimo), CLAUDE.md, GEMINI.md, .hermes.md, .github/copilot-instructions.md (+ AGENTS.md) для copilot.
- Тесты: `tests/core/test_low_level.py` — `test_generate_skills_metadata*` (104-440), особенно `..._includes_navigation_rules_refs` (237), `..._hints_merge_and_contextual_ignored` (291), `..._global_hints_from_all_extensions` (336); `tests/ide/test_registry.py` — рендер.
- Hint-бюджеты: `_finalize_hints_for_skill_metadata` (low_level.py:237) — остаются для `hints.local`.
- `validate_rendered_identity` использует `generate_skills_metadata` — поведению не мешает.

## Design overview
- Affected modules: `spawn_cli.core.low_level` (метаданные скиллов), `spawn_cli.ide._helpers` (рендер), все 11 IDE-адаптеров (передача имени entry-файла).
- Files & symbols:
  - `src/spawn_cli/core/low_level.py` — `generate_skills_metadata`
  - `src/spawn_cli/ide/_helpers.py` — `render_skill_md`, `_mandatory_reads_for_render` (удаляется), `_NAV_YAML_FILE`/`_NAV_YAML_DESCRIPTION` (удаляются)
  - 11 файлов `src/spawn_cli/ide/*.py` — вызовы `render_skill_md`
- Data flow changes: метаданные скилла = skill-local; рендер получает имя entry-файла адаптера и печатает инструкцию прочитать его.
- Integration points: адаптеры через `registry.render_skill_md`; `_required_read_description_for_path` остаётся для описаний локальных файлов.

## Before → After
### Before
- Скилл: frontmatter, body, Hints (global+local+maintainer, с truncation), Mandatory reads (skill + local + global + nav rules + буллет navigation.yaml), Contextual reads (local + global + nav contextual).
### After
- Скилл: frontmatter, body, инструкция прочитать entry point (если не загружен), Hints (только hints.local, бюджет сохранён), Mandatory reads (skill required-read + localRead владельца), Contextual reads (только localRead:auto владельца).

## Details
- Формат инструкции (после body, до Hints), одна строка:
  `Before this skill, if the Spawn block instructions from `{entry_file}` are not loaded, read `{entry_file}` first.`
- entry_file на адаптер: agents-md адаптеры — `AGENTS.md`; claude_code — `CLAUDE.md`; gemini_cli — `GEMINI.md`; hermes — `.hermes.md`; github_copilot — `.github/copilot-instructions.md`.
- Убираемые источники дублирования (все уже в entry-блоке после задачи 32): `merged_global_required`, `merged_global_auto`, `nav_rules_required`, `nav_rules_contextual`, `global_streams`, `maintainer_hints`.
- Хелперы: `_merge_hint_streams_ordered`, `_extension_global_hint_streams_ordered`, `_navigation_read_required_rule_hints_ordered` остаются в использовании (navigation/AGENTS-rollup пайплайн). `_navigation_yaml_rules_refs` / `_navigation_rules_refs_from_section` и `_flatten_global_refs_ordered` после изменения становятся мёртвым кодом (производственных вызовов нет) — удалены. `get_required_read_global_all` / `get_auto_read_global_all` экспортируются через `__all__` (публичный API) — оставить без изменений, внутренних вызовов после задачи не остаётся.
- `_required_read_description_for_path`: мёртвый параметр `nav_rules_required` удалён; вызывается с `merged_global=[]`, `local_req`, `cfg_ext` — локальные описания сохраняются.
- github_copilot пишет Spawn-блок в два файла; в инструкции скилла указываем `.github/copilot-instructions.md` (приоритетный для Copilot) — осознанный выбор, AGENTS.md у копилота вторичен.

## Execution Scheme
Suggested coordinator model: glm-5.3
> Each step id is the subtask filename (e.g. `1-skill-local-metadata`).
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-skill-local-metadata → step 2-render-entry-instruction → step 3-update-tests → step 4-update-design-docs
- Phase 2 (sequential): step review — inspect all changes, fix inconsistencies
