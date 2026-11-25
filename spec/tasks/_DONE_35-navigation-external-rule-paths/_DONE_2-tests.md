# Step 2: Tests for external rule paths and comment preservation

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Pin the new semantics with focused tests.

## Approach
Extend tests/core/test_low_level.py. Use the file's existing conventions: `ll`, `warnings`, `YAML_W` (ruamel YAML instance) — no new imports.

## Affected files
- `tests/core/test_low_level.py` — new test functions

## Code changes (before / after)

### `tests/core/test_low_level.py` — new tests (insert after test_save_rules_navigation_missing_rule_warns, ~line 665)

**Before**
No coverage: non-rules existing paths, missing external path warning, escaping path rejection, comment preservation for save_rules_navigation.

**After**
```python
def test_save_rules_navigation_keeps_external_existing_path(tmp_path):
    (tmp_path / "spawn" / "rules").mkdir(parents=True)
    (tmp_path / "spec" / "design").mkdir(parents=True)
    (tmp_path / "spec" / "design" / "hla.md").write_text("# HLA", encoding="utf-8")
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text(
        "read-required:\n"
        "- rules:\n"
        "  - path: spec/design/hla.md\n"
        "    description: HLA doc.\n"
        "  - path: spawn/rules/team.yaml\n"
        "    description: Local rule file.\n",
        encoding="utf-8",
    )
    ll.save_rules_navigation(tmp_path)
    data = YAML_W.load(nav.read_text(encoding="utf-8"))
    paths = [r["path"] for r in data["read-required"][0]["rules"]]
    assert "spec/design/hla.md" in paths

def test_save_rules_navigation_prunes_missing_external_path_with_warning(tmp_path):
    (tmp_path / "spawn" / "rules").mkdir(parents=True)
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text(
        "read-required:\n"
        "- rules:\n"
        "  - path: spec/design/gone.md\n"
        "    description: gone.\n",
        encoding="utf-8",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ll.save_rules_navigation(tmp_path)
    assert any("Removed missing rule path" in str(w.message) for w in caught)
    data = YAML_W.load(nav.read_text(encoding="utf-8"))
    rules = data["read-required"][0]["rules"]
    assert all(r["path"] != "spec/design/gone.md" for r in rules)

def test_save_rules_navigation_rejects_escaping_path(tmp_path):
    (tmp_path / "spawn" / "rules").mkdir(parents=True)
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text(
        "read-required:\n"
        "- rules:\n"
        "  - path: ../outside.md\n"
        "    description: escape.\n",
        encoding="utf-8",
    )
    ll.save_rules_navigation(tmp_path)
    data = YAML_W.load(nav.read_text(encoding="utf-8"))
    rules = data["read-required"][0]["rules"]
    assert all(r["path"] != "../outside.md" for r in rules)

def test_save_rules_navigation_rejects_absolute_path(tmp_path):
    (tmp_path / "spawn" / "rules").mkdir(parents=True)
    nav = tmp_path / "spawn" / "navigation.yaml"
    outside = tmp_path.parent / "abs.md"
    nav.write_text(
        "read-required:\n"
        f"- rules:\n  - path: {outside}\n    description: abs.\n",
        encoding="utf-8",
    )
    ll.save_rules_navigation(tmp_path)
    data = YAML_W.load(nav.read_text(encoding="utf-8"))
    rules = data["read-required"][0]["rules"]
    assert all("abs.md" not in str(r["path"]) for r in rules)

def test_save_rules_navigation_preserves_comments(tmp_path):
    (tmp_path / "spawn" / "rules").mkdir(parents=True)
    (tmp_path / "spawn" / "rules" / "team.yaml").write_text("x: 1", encoding="utf-8")
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text(
        "# top comment\n"
        "read-required:\n"
        "- rules:\n"
        "  - path: spawn/rules/team.yaml # inline comment\n"
        "    description: Local rule file.\n",
        encoding="utf-8",
    )
    ll.save_rules_navigation(tmp_path)
    text = nav.read_text(encoding="utf-8")
    assert "# top comment" in text
```
Inline comment on a mutated entry: ruamel keeps entry-level comments via in-place mutation; if the inline comment on the `path` line is dropped by rt round-trip in this configuration, assert only the top comment (implementation may relax that assertion after observing actual behavior).

## Additional actions
- Run: `python -m pytest tests/core/test_low_level.py -k "save_rules_navigation" -x`
- Then full suite: `python -m pytest tests/ -q`
