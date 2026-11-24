# Step 1: generate_skills_metadata — только skill-local контекст

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Метаданные скилла содержат только skill `required-read`, `localRead` владельца и `hints.local`.

## Approach
Переписать тело `generate_skills_metadata` в `src/spawn_cli/core/low_level.py`. Хелперы глобальных потоков не удалять — они нужны navigation-пайплайну.

## Affected files
- `src/spawn_cli/core/low_level.py` — функция `generate_skills_metadata` (строки 546-625).

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — `generate_skills_metadata`

**Before**
```python
def generate_skills_metadata(target_root: Path, extension: str) -> list[SkillMetadata]:
    cfg_ext = _load_ext_config(target_root, extension)
    maintainer_hints = _navigation_read_required_rule_hints_ordered(target_root)
    global_streams = _extension_global_hint_streams_ordered(target_root)
    local_raw = list(cfg_ext.hints.local) if cfg_ext.hints else []
    merged_for_skill = _merge_hint_streams_ordered(
        [*global_streams, local_raw, maintainer_hints]
    )
    skill_hints = (
        _finalize_hints_for_skill_metadata(merged_for_skill) if merged_for_skill else []
    )

    merged_global_required = _flatten_global_refs_ordered(
        target_root, get_required_read_global_all(target_root)
    )
    merged_global_auto = _flatten_global_refs_ordered(target_root, get_auto_read_global_all(target_root))
    local_required = get_required_read_ext_local(target_root, extension)
    local_auto = get_auto_read_local(target_root, extension)
    nav_rules_required, nav_rules_contextual = _navigation_yaml_rules_refs(target_root)
```
Собирает hints (global + local + maintainer) и глобальные/nav риды для вливания в каждый скилл.

**After**
```python
def generate_skills_metadata(target_root: Path, extension: str) -> list[SkillMetadata]:
    cfg_ext = _load_ext_config(target_root, extension)
    local_raw = list(cfg_ext.hints.local) if cfg_ext.hints else []
    skill_hints = (
        _finalize_hints_for_skill_metadata(local_raw) if local_raw else []
    )

    local_required = get_required_read_ext_local(target_root, extension)
    local_auto = get_auto_read_local(target_root, extension)
```
Hints скилла — только `hints.local` владельца (бюджеты truncation сохраняются в `_finalize_hints_for_skill_metadata`). Глобальные риды и nav-дубли больше не попадают в скиллы: они целиком во встроенном navigation entry-блока (задача 32).

**Before** (тело цикла по required, строки ~566-594)
```python
        for blob in (
            list(raw.required_read),
            [r.file for r in local_required],
            [r.file for r in merged_global_required],
        ):
            for fp in blob:
                nk = _norm_read_path(fp)
                if nk in seen_norm:
                    continue
                seen_norm.add(nk)
                required_paths.append(fp)
        for ref in nav_rules_required:
            nk = _norm_read_path(ref.file)
            if nk in seen_norm:
                continue
            seen_norm.add(nk)
            required_paths.append(ref.file)

        required_out = [
            SkillFileRef(
                file=p,
                description=_required_read_description_for_path(
                    p, merged_global_required, local_required, cfg_ext, nav_rules_required
                ),
            )
            for p in required_paths
        ]
```
Required = skill + local + global + nav rules.

**After**
```python
        for blob in (list(raw.required_read), [r.file for r in local_required]):
            for fp in blob:
                nk = _norm_read_path(fp)
                if nk in seen_norm:
                    continue
                seen_norm.add(nk)
                required_paths.append(fp)

        required_out = [
            SkillFileRef(
                file=p,
                description=_required_read_description_for_path(
                    p, [], local_required, cfg_ext
                ),
            )
            for p in required_paths
        ]
```
Required = skill required-read + localRead владельца.

**Before** (тело цикла по auto, строки ~600-619)
```python
        for ar in local_auto:
            ...
        for ar in merged_global_auto:
            ...
        for ar in nav_rules_contextual:
            ...
```
Auto = local + global + nav contextual.

**After**
```python
        for ar in local_auto:
            key = _norm_read_path(ar.file)
            if key in required_key_set or key in seen_auto:
                continue
            seen_auto.add(key)
            auto_out.append(ar)
```
Auto = только localRead:auto владельца (исключая required-ключи).

## Additional actions
- Удалить `_flatten_global_refs_ordered` (после изменения — мёртвый код, единственный вызов был в `generate_skills_metadata`). `get_required_read_global_all` / `get_auto_read_global_all` — публичный API (`__all__`), оставить; их вызовы из `generate_skills_metadata` убрать.
- `_merge_hint_streams_ordered`, `_extension_global_hint_streams_ordered`, `_navigation_read_required_rule_hints_ordered`, `_navigation_yaml_rules_refs` НЕ трогать — используются `rollup_hints_for_agents` и navigation-пайплайном (low_level.py:297-302).
