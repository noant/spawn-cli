# Step 3: Обновление дизайн-документа agentic-flow.md

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
`spec/design/agentic-flow.md` отражает новый контракт entrypoint: контент navigation.yaml встраивается в блок вместо ссылки на файл.

## Approach
Обновить секции Startup Flow и Entrypoint Contract в `spec/design/agentic-flow.md`. Не менять другие секции (Skill Flow и пр. — ссылка на чтение navigation в skill flow остаётся корректной, т.к. рендер навыков не меняется).

## Affected files
- `spec/design/agentic-flow.md` — секции `Startup Flow` (шаг 1) и `Entrypoint Contract`.

## Code changes (before / after)

### `spec/design/agentic-flow.md` — Startup Flow, шаг 1

**Before**
```markdown
1. Read `spawn/navigation.yaml`.
2. Read every file listed under `read-required`.
```
Инструкция прочитать navigation.yaml первым шагом.

**After**
```markdown
1. Spawn embeds the full content of `spawn/navigation.yaml` into the IDE
   entrypoint block; agents read it directly from the entry file.
2. Read every file listed under `read-required`.
```
Контент navigation доступен в entry-блоке; отдельное чтение файла не требуется.

### `spec/design/agentic-flow.md` — Entrypoint Contract

**Before**
```markdown
```markdown
Before working, read `spawn/navigation.yaml`.
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the
current task.
```
```
Контракт блока с ссылкой на файл.

**After**
```markdown
```markdown
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the
current task.

spawn/navigation.yaml:
```yaml
<full merged navigation.yaml content>
```
```

When `spawn/navigation.yaml` is missing, refresh emits `SpawnError` instead of
rendering an empty block.
```
Контракт: инструкции + полный yaml-контент navigation; Hints (при наличии) идут после yaml-блока; контент navigation не входит в hint-budget.

## Additional actions
- Проверить целостность markdown после правки.
