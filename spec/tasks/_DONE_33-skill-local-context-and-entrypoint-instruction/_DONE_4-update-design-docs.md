# Step 4: Обновление дизайн-документов

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Дизайн-доки отражают: скиллы несут только skill-local контекст + инструкцию entry point.

## Approach
Обновить `spec/design/agentic-flow.md` (Skill Flow, Skill Metadata Generation, Hints in rendered skills, Rendered Skills), `spec/design/ide-adapters.md` (контракт рендера скиллов), `spec/design/utility-method-flows.md` (generate-skills-metadata flow), при необходимости `spec/design/extensions.md` (если описывает localRead в скиллах).

## Affected files
- `spec/design/agentic-flow.md` — секции `Skill Flow`, `Skill Metadata Generation`, `Rendered Skills`.
- `spec/design/ide-adapters.md` — рендер скиллов: hints-композиция (строка ~138) и контракт "navigation.yaml exactly once, always last" (строка ~199).
- `spec/design/utility-method-flows.md` — §generate-skills-metadata.
- `spec/design/hla.md` — строка ~51 "Mandatory reads with spawn/navigation.yaml last".
- `spec/design/extension-author-guide.md` — строка ~210: порядок рендера скилла и мерж hints.

## Code changes (before / after)

### `spec/design/agentic-flow.md` — Skill Flow

**Before**
```markdown
3. Follow the skill body and any **Hints** list rendered in the skill file.
```
и абзац "Spawn rendering also duplicates paths from `spawn/navigation.yaml` **rules** groups into each skill's mandatory reads ... with the same path-normalization and dedup rules as navigation".

**After**
```markdown
3. Follow the skill body, the entrypoint instruction (read the IDE entry file
   when its Spawn block is not loaded), and any **Hints** list rendered in
   the skill file.
```
Абзац про дублирование rules-групп в скиллы заменить на: скиллы не дублируют navigation; глобальные риды и hints читаются из entry-блока (задача 32), скилл ссылается на entry-файл инструкцией.

### `spec/design/agentic-flow.md` — Skill Metadata Generation

**Before**
```text
required = distinct(
  skill_info.required-read +
  local_required +
  global_required
)
auto = distinct(local_auto + global_auto)
```
и hints-абзац (global streams + maintainer hints).

**After**
```text
required = distinct(skill_info.required-read + local_required)
auto = distinct(local_auto)
```
hints: только `hints.local` владельца скилла (бюджеты truncation сохранены); `hints.global` и maintainer-hints живут только в entry-блоке (AGENTS.md rollup).

### `spec/design/agentic-flow.md` — Rendered Skills (пример)

**Before**
```markdown
Mandatory reads:
- `spec/main.md` - Spec task process.
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).
```

**After**
```markdown
Before this skill, if the Spawn block instructions from `AGENTS.md` are not
loaded, read `AGENTS.md` first.

Mandatory reads:
- `spec/main.md` - Spec task process.
```
(пример; entry-файл зависит от IDE адаптера). Список требований к rendered skill: убрать пункт "spawn/navigation.yaml listed once, last"; добавить пункт про entrypoint instruction.

## Additional actions
- Синхронизировать `ide-adapters.md` (hints-композиция ~138, контракт рендера ~199), `utility-method-flows.md` (§generate-skills-metadata), `hla.md` (~51) и `extension-author-guide.md` (~210) с теми же изменениями: скиллы не содержат глобальных ридов/hints и nav-дубликатов; entry-инструкция ссылается на entry-файл адаптера.
