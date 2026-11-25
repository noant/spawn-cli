# Step 1: Prune by existence only + round-trip YAML

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Keep navigation rules rows for any existing repo-relative file; preserve comments.

## Approach
Edit src/spawn_cli/core/low_level.py only. Mutate existing entries in place (preserves row comments); module-level containment+file helper.

## Affected files
- `src/spawn_cli/core/low_level.py` — save_rules_navigation, prune_read_required_rules, prune_contextual_rules

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — prune_read_required_rules, exists check

**Before**
```python
rk = posix_norm(path_raw.strip())
exists = rk in paths_on_disk and (Path(target_root) / Path(rk)).is_file()
```
Restricts rows to spawn/rules/; external existing files pruned as "missing".

**After**
```python
rk = posix_norm(path_raw.strip())
exists = _nav_path_exists_within_repo(target_root, rk)
```
Row kept for any existing file inside the repo root.

### `src/spawn_cli/core/low_level.py` — prune_read_required_rules, kept row built as new dict

**Before**
```python
row: dict[str, Any] = {
    'path': rk,
    'description': str(entry.get('description') or 'Local rule file.'),
}
out.append(row)
```
New dict drops entry-level comment metadata.

**After**
```python
entry['path'] = rk
entry['description'] = str(entry.get('description') or 'Local rule file.')
out.append(entry)
```
In-place mutation preserves comments (CommentedMap and plain dict both).

### `src/spawn_cli/core/low_level.py` — prune_contextual_rules, exists check and kept row

**Before**
```python
rk = posix_norm(str(entry['path']))
exists = rk in paths_on_disk and (Path(target_root) / Path(rk)).is_file()
if exists:
    row: dict[str, Any] = {
        'path': rk,
        'description': str(entry.get('description') or 'Local rule file.'),
    }
    hint_val = entry.get('hint')
    if isinstance(hint_val, str):
        row['hint'] = hint_val
    out.append(row)
```

**After**
```python
rk = posix_norm(str(entry['path']))
exists = _nav_path_exists_within_repo(target_root, rk)
if exists:
    entry['path'] = rk
    entry['description'] = str(entry.get('description') or 'Local rule file.')
    out.append(entry)
```
Hint is part of entry already; no rebuild.

### `src/spawn_cli/core/low_level.py` — new module-level helper (place before save_rules_navigation)

**Before**
No such symbol; membership check inline.

**After**
```python
def _nav_path_exists_within_repo(target_root: Path, rel_posix: str) -> bool:
    """True when rel_posix is a repo-relative file path (no absolute, no escape) that exists."""
    if not rel_posix or Path(rel_posix).is_absolute():
        return False
    resolved = (Path(target_root) / Path(rel_posix)).resolve()
    root = Path(target_root).resolve()
    return resolved.is_file() and (root == resolved or root in resolved.parents)
```

### `src/spawn_cli/core/low_level.py` — save_rules_navigation, load

**Before**
```python
def save_rules_navigation(target_root: Path) -> None:
    nav_path = _spawn(target_root) / 'navigation.yaml'
    raw = load_yaml(nav_path) or {}
    rr: list[Any] = list(raw['read-required']) if isinstance(raw.get('read-required'), list) else []
    rc: list[Any] = list(raw.get('read-contextual')) if isinstance(raw.get('read-contextual'), list) else []
```
Safe YAML drops comments; list() copies drop sequence metadata.

**After**
```python
def save_rules_navigation(target_root: Path) -> None:
    nav_path = _spawn(target_root) / 'navigation.yaml'
    yaml_rt = YAML(typ="rt")
    configure_yaml_dump(yaml_rt)
    if nav_path.is_file():
        with nav_path.open("r", encoding="utf-8") as fh:
            raw = yaml_rt.load(fh)
    else:
        raw = None
    if raw is None or not isinstance(raw, dict):
        from ruamel.yaml.comments import CommentedMap

        raw = CommentedMap()
    rr: list[Any] = raw.get('read-required')
    if not isinstance(rr, list):
        rr = []
        raw['read-required'] = rr
    rc: list[Any] = raw.get('read-contextual')
    if not isinstance(rc, list):
        rc = []
        raw['read-contextual'] = rc
```

### `src/spawn_cli/core/low_level.py` — save_rules_navigation, write-back (also remove the now-redundant reassignments `raw["read-required"] = rr` / `raw["read-contextual"] = rc` before it)

**Before**
```python
    raw["read-required"] = rr
    raw["read-contextual"] = rc
    _ensure_navigation_root_key_order(raw)
    save_yaml(nav_path, raw)
```

**After**
```python
    _ensure_navigation_root_key_order(raw)
    ensure_dir(nav_path.parent)
    with nav_path.open("w", encoding="utf-8") as fh:
        yaml_rt.dump(raw, fh)
```
Round-trip dump preserves comments; sections reused in place.

## Additional actions
- Run: `python -m pytest tests/core/test_low_level.py -k save_rules_navigation -x`
