# Step 1: Встраивание контента navigation.yaml в entrypoint prompt

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
`refresh_entry_point` рендерит полный текст `spawn/navigation.yaml` в Spawn-блок entrypoint.

## Approach
Изменить константу и функцию в `src/spawn_cli/core/high_level.py`. Не трогать адаптеры и `_helpers.py`.

## Affected files
- `src/spawn_cli/core/high_level.py` — константа `SPAWN_ENTRY_POINT_PROMPT`, функция `refresh_entry_point`.

## Code changes (before / after)

### `src/spawn_cli/core/high_level.py` — `SPAWN_ENTRY_POINT_PROMPT`

**Before**
```python
SPAWN_ENTRY_POINT_PROMPT = """\
Before working, read `spawn/navigation.yaml`.
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the current task.
"""
```
Базовый текст блока: инструкция прочитать navigation.yaml.

**After**
```python
SPAWN_ENTRY_POINT_PROMPT = """\
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the current task.
"""
```
Инструкция прочитать navigation.yaml удалена: контент файла рендерится ниже в блоке.

### `src/spawn_cli/core/high_level.py` — `refresh_entry_point`

**Before**
```python
def refresh_entry_point(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    rollup = ll.rollup_hints_for_agents(target_root)
    ll.warn_if_agents_hints_exceed_measurement(rollup)
    if rollup:
        prompt = (
            f"{SPAWN_ENTRY_POINT_PROMPT}\nHints:\n"
            + "\n".join(f"- {h}" for h in rollup)
            + "\n"
        )
    else:
        prompt = SPAWN_ENTRY_POINT_PROMPT
    ide_get(ide).rewrite_entry_point(target_root, prompt)
```
Собирает prompt из константы и rollup hints.

**After**
```python
def _navigation_content_section(target_root: Path) -> str:
    nav_path = target_root / "spawn" / "navigation.yaml"
    if not nav_path.is_file():
        raise SpawnError("spawn/navigation.yaml is missing; run spawn refresh")
    content = nav_path.read_text(encoding="utf-8").rstrip("\n")
    return f"spawn/navigation.yaml:\n```yaml\n{content}\n```\n"


def refresh_entry_point(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    rollup = ll.rollup_hints_for_agents(target_root)
    ll.warn_if_agents_hints_exceed_measurement(rollup)
    nav = _navigation_content_section(target_root)
    prompt = SPAWN_ENTRY_POINT_PROMPT + "\n" + nav
    if rollup:
        prompt += "\nHints:\n" + "\n".join(f"- {h}" for h in rollup) + "\n"
    ide_get(ide).rewrite_entry_point(target_root, prompt)
```
Prompt: инструкции, полный yaml-контент navigation в fenced-блоке, затем опционально Hints. Контент navigation не попадает в hint-budget.

## Additional actions
- Проверить, что `SpawnError` уже импортирован в модуле (строка `from spawn_cli.core.errors import SpawnError, SpawnWarning` — есть).
