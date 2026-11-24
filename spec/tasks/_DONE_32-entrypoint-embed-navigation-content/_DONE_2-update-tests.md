# Step 2: Обновление тестов entrypoint

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Тесты `refresh_entry_point` отражают новый формат prompt с полным контентом navigation.yaml.

## Approach
Обновить существующий тест в `tests/core/test_high_level.py`, добавить тест на отсутствие navigation.yaml. Сохранить существующий паттерн мока: декоратор `@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())` + внутренний `patch(..., return_value=mock)` с `MagicMock(wraps=_stub_ide())` (важно: патчить `spawn_cli.core.high_level.ide_get`, а не `spawn_cli.ide.registry.get`).

## Affected files
- `tests/core/test_high_level.py` — тест `test_refresh_entry_point` (строка ~487); новый тест `test_refresh_entry_point_missing_navigation` рядом.

## Code changes (before / after)

### `tests/core/test_high_level.py` — `test_refresh_entry_point`

**Before**
```python
@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_entry_point(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    mock = MagicMock(wraps=_stub_ide())
    with patch("spawn_cli.core.high_level.ide_get", return_value=mock):
        hl.refresh_entry_point(target, "cursor")
    mock.rewrite_entry_point.assert_called_once()
    assert hl.SPAWN_ENTRY_POINT_PROMPT in mock.rewrite_entry_point.call_args[0][1]
```
Проверяет только наличие константы в prompt.

**After**
```python
@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_entry_point(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    mock = MagicMock(wraps=_stub_ide())
    with patch("spawn_cli.core.high_level.ide_get", return_value=mock):
        hl.refresh_entry_point(target, "cursor")
    mock.rewrite_entry_point.assert_called_once()
    prompt = mock.rewrite_entry_point.call_args[0][1]
    assert hl.SPAWN_ENTRY_POINT_PROMPT in prompt
    nav_content = (target / "spawn" / "navigation.yaml").read_text(encoding="utf-8")
    assert "spawn/navigation.yaml:" in prompt
    assert nav_content in prompt
    assert "Before working, read" not in prompt
```
Дополнительно проверяет: заголовок секции, полный контент navigation в prompt, отсутствие старой строки-ссылки.

### `tests/core/test_high_level.py` — новый тест отсутствия navigation

**Before**
```
```
Теста нет.

**After**
```python
@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_entry_point_missing_navigation(target: Path) -> None:
    (target / "spawn" / "navigation.yaml").unlink()
    with pytest.raises(SpawnError):
        hl.refresh_entry_point(target, "cursor")
```
Фикстура `target` инициализирует репо через `ll.init` (navigation.yaml создан); удаляем файл и ожидаем SpawnError. Импорты `pytest` и `SpawnError` уже присутствуют в файле тестов — изменений не требуется.

Остальные два теста (`..._hints_rollup_skips_local`, `..._agents_warnings_for_oversize_hint`) не требуют изменений: они проверяют Hints-часть, которая остаётся после yaml-блока, и assert `SPAWN_ENTRY_POINT_PROMPT in prompt` остаётся валидным.

## Additional actions
- Прогнать весь файл тестов: `pytest tests/core/test_high_level.py -q`.
