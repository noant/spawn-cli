# 32: Полный контент spawn/navigation.yaml в Spawn-блоке entrypoint

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
- [ ] Design document update [glm-5.3]

## Goal
В Spawn-managed блоке IDE entrypoint (AGENTS.md и аналоги) рендерить целиком содержимое `spawn/navigation.yaml` вместо ссылки на файл.

## Motivation
Рефакторинг UX для агентов: агент получает всю навигацию сразу в entry-файле и не тратит отдельный шаг на чтение `spawn/navigation.yaml`.

## Invasiveness level
minimally-invasive

## Review models
- Research review: single agent: glm-5.3-flash
- Spec review: cross-review: deepseek-v4-pro, glm-5.3
- Code review: cross-review: deepseek-v4-pro, glm-5.3

## Run mode
auto

## Research summary
- Entry prompt константа: `SPAWN_ENTRY_POINT_PROMPT` в `src/spawn_cli/core/high_level.py` (строки 18-22).
- Рендер блока: `refresh_entry_point(target_root, ide)` в `src/spawn_cli/core/high_level.py` (строки ~194-210) — собирает prompt (константа + опционально `Hints:`) и передаёт в `ide_get(ide).rewrite_entry_point(target_root, prompt)`.
- Адаптеры (cursor, codex, claude_code и др.) пишут prompt как есть в managed-блок (`<!-- spawn:start -->` ... `<!-- spawn:end -->`) через `rewrite_managed_block` из `src/spawn_cli/ide/_helpers.py`.
- `spawn/navigation.yaml` пишется `save_yaml` (`src/spawn_cli/io/yaml_io.py`), читается `load_yaml` по пути `spawn/navigation.yaml` (паттерн в `low_level._navigation_yaml_rules_refs` и др.).
- Тесты: `tests/core/test_high_level.py` — `test_refresh_entry_point` (строка 488), `test_refresh_entry_point_hints_rollup_skips_local` (498), `test_refresh_entry_point_agents_warnings_for_oversize_hint` (532).
- Дизайн-контракт блока описан в `spec/design/agentic-flow.md` (Entrypoint Contract) — потребуется обновление в Step 8.

## Design overview
- Affected modules: `spawn_cli.core.high_level` (сборка prompt entrypoint), тесты.
- Files & symbols:
  - `src/spawn_cli/core/high_level.py` — константа `SPAWN_ENTRY_POINT_PROMPT`, функция `refresh_entry_point`.
- Data flow changes: `refresh_entry_point` читает текст `spawn/navigation.yaml` и вставляет его в prompt (после инструкций, до `Hints:`); адаптеры без изменений.
- Integration points: все IDE-адаптеры через `IdeCapabilities.rewrite_entry_point` — изменения прозрачны (prompt передаётся как строка).

## Before → After
### Before
- Managed-блок entrypoint содержит текст "Before working, read `spawn/navigation.yaml`." + списки правил чтения + опционально Hints. Агент должен отдельно читать navigation.yaml.
### After
- Managed-блок содержит те же инструкции (без указания читать navigation.yaml), затем целиком контент `spawn/navigation.yaml` в fenced yaml-блоке, затем опционально Hints.

## Details
- Формат блока:
  1. Строки инструкций (read-required обязателен, read-contextual по релевантности) — убрать строку "Before working, read `spawn/navigation.yaml`.".
  2. Пустая строка, заголовок `spawn/navigation.yaml:`, затем fenced-блок ```yaml с полным текстом файла.
  3. Пустая строка и `Hints:` (как сейчас), если rollup непуст.
- Чтение файла: `Path.read_text` по `target_root / "spawn" / "navigation.yaml"`. Файл создаётся при `ll.init` и refresh навигации; при отсутствии файла (рассинхрон) — SpawnError, а не тихий пустой блок.
- Предупреждение об oversize hints не меняется; контент navigation в бюджет hints не входит.

## Execution Scheme
Suggested coordinator model: glm-5.3
> Each step id is the subtask filename (e.g. `1-embed-navigation`).
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-embed-navigation → step 2-update-tests → step 3-update-design-doc
- Phase 2 (sequential): step review — inspect all changes, fix inconsistencies
