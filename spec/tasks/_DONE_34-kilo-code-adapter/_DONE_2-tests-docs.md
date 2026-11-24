# Step 2: Tests and docs for the Kilo Code adapter

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Cover the new adapter with tests mirroring the precedent adapters and update the adapter documentation.

## Approach
Tests mirror `tests/ide/test_cline.py` (ignore/entry/vacancy), `tests/ide/test_mimo_code.py` (MCP config round-trips), and add registry/parity entries (checklist items 9-10). Docs: extend the matrix and lists in `spec/design/ide-adapters.md`, the adapter list in `spec/design/hla.md`, and the README adapter table row.

## Affected files
- `tests/ide/test_kilo_code.py` - new test module (`KiloCodeAdapter` fixture, `_skill` helper)
- `tests/ide/test_registry.py` - imports + `get("kilo-code")` / `get("kilo")` assertions + `ADAPTER_ENTRY_FILES` entry
- `tests/ide/test_mcp_stdio_proxy_parity.py` - parametrize entry `kilo_json`
- `spec/design/ide-adapters.md` - canonical key list, alias list, IDE Matrix row, entry-point table row, agent-ignore table row, OpenCode JSON Shape paragraph mention
- `spec/design/hla.md` - concrete adapters list
- `README.md` - adapter table row (line ~238-240 block)

## Code changes (before / after)

### `tests/ide/test_kilo_code.py` — new tests
**Before**
(no file)
**After**
Mirror `test_cline.py` + `test_mimo_code.py`, adapted:
- `test_detect_markers`: False on empty; True for `.kilo/`, `.kilocode/`, `kilo.json`, `kilo.jsonc` (subdir markers like test_cline does).
- `test_capabilities`: skills native, mcp project, agent_ignore native, entry_point agents-md.
- `test_add_and_remove_skills`: name "My Skill" renders `.kilo/skills/my-skill/SKILL.md`, `name: my-skill` in frontmatter; remove prunes the dir.
- `test_sanitize_skill_name`: `_sanitize_skill_name("a.b_c") == "a-b-c"` (dots/underscores become hyphens; rule 04); long name: 80-char input truncated to 64 with no trailing hyphen.
- `test_remove_skills_keeps_extra_files` (same as cline).
- `test_add_skills_warns_on_overwrite` (SpawnWarning).
- `test_add_mcp_and_remove_mcp`: `NormalizedMcp` stdio server `command="uvx"` -> `.kilo/kilo.json` `{"mcp": {"srv": {"type": "local", "command": ["uvx"], "enabled": true}}}`; remove_mcp pops key and empty `mcp`; file left as `{}`.
- `test_mcp_unparseable_errors_before_mutation`: write invalid JSON to `.kilo/kilo.json`, `pytest.raises(SpawnError)` on `add_mcp`, file content unchanged (rule 05).
- `test_jsonc_variant_warns`: create `.kilo/kilo.jsonc` and/or root `kilo.json`, `pytest.warns(SpawnWarning, match="kilo.json")` on `add_mcp` (naming the unmanaged variant files).
- `test_agent_ignore_roundtrip` / `_idempotent` / `_legacy_block_migrates` / `_split_and_clear` on `.kilocodeignore` (same as cline).
- `test_entry_point_creates_and_replaces` -> "AGENTS.md" (same as cline).
- `test_finalize_removes_vacant_kilo`: add skill + core ignore, remove skill, clear ignore, finalize -> no `.kilo`, no `.kilocodeignore`.
- `test_finalize_keeps_user_content`: `.kilo/rules/keep.md` kept; user line in `.kilocodeignore` kept; user key in kilo.json (e.g. `"instructions": [...]`) keeps the file.
- `test_finalize_removes_vacant_legacy_kilocode_dir`: empty `.kilocode/` dir is dropped.

### `tests/ide/test_registry.py` — assertions
**Before**
```python
    JunieAdapter,
    MimoCodeAdapter,
```
**After**
```python
    JunieAdapter,
    KiloCodeAdapter,
    MimoCodeAdapter,
```
Add to `test_get_known_adapter`:
```python
    assert isinstance(get("kilo-code"), KiloCodeAdapter)
    assert get("kilo-code").key == "kilo-code"
```
Add to `test_get_alias`:
```python
    k = get("kilo")
    assert k.key == "kilo-code"
    assert isinstance(k, KiloCodeAdapter)
```
Add to `ADAPTER_ENTRY_FILES` (keep class-name sort; insert between `JunieAdapter` and `MimoCodeAdapter`):
```python
    (KiloCodeAdapter, "AGENTS.md"),
```

### `tests/ide/test_mcp_stdio_proxy_parity.py` — parametrize
**Before**
```python
        pytest.param(JunieAdapter(), "junie_json", id="junie"),
    ],
)
```
**After**
```python
        pytest.param(JunieAdapter(), "junie_json", id="junie"),
        pytest.param(KiloCodeAdapter(), "kilo_json", id="kilo_code"),
    ],
)
```
Add import `from spawn_cli.ide.kilo_code import KiloCodeAdapter`; add branch:
```python
    elif read_entries == "kilo_json":
        data = json.loads((tmp_path / ".kilo" / "kilo.json").read_text(encoding="utf-8"))
        inline_entry = dict(data["mcp"][inline.name])
        proxy_entry = dict(data["mcp"][proxied.name])
```
and include `"kilo_json"` in the opencode-style golden check tuple `("opencode_json", "mimocode_json", "kilo_json")`.

### `spec/design/ide-adapters.md` — docs
**Before**
```markdown
- `junie`
```
(canonical list) and
```text
mimo -> mimo-code
```
(aliases)
**After**
```markdown
- `junie`
- `kilo-code`
```
and
```text
mimo -> mimo-code
kilo -> kilo-code
```
New IDE Matrix row:
```markdown
| Kilo Code | `.kilo/skills/{skill}/SKILL.md` (frontmatter `name` must equal directory name; stricter name regex `^[a-z0-9]+(-[a-z0-9]+)*$` max 64 chars — `.`/`_` sanitized to `-` by the adapter) | `.kilo/kilo.json` key `mcp` (same local/remote + `enabled` shape as OpenCode/Mimo; `{env:VAR}` placeholders) | `.kilocodeignore` (repo root, gitignore-style; file keeps the legacy kilocode prefix) | `AGENTS.md` | Detection markers: `.kilo/`, legacy `.kilocode/`, root `kilo.json`/`kilo.jsonc` (`AGENTS.md` alone is NOT a marker — shared). Canonical config `.kilo/kilo.json`; warns (SpawnWarning) when only `kilo.jsonc` exists; unparseable JSON errors before mutation. Kilo also auto-loads `.agents/skills`/`.claude/skills` (compat — outside this column). Vacancy pruner `finalize_kilo_code_repo` (known key `mcp`). |
```
Entry-point table row: `| Kilo Code | AGENTS.md |` after JetBrains Junie. Agent-ignore table row:
```markdown
| Kilo Code | Merge Spawn-owned globs into `.kilocodeignore` (repo root, gitignore syntax) via the managed block; split-region overrides and `clear_spawn_agent_ignore` supported, mirroring Cline. |
```
OpenCode JSON Shape section: extend the Mimo paragraph — "Kilo Code uses the same shape in `.kilo/kilo.json` (canonical JSON; JSONC sibling not merged)."

### `spec/design/hla.md` — adapters list
**Before**
```markdown
- **Concrete adapters** (Cursor, Codex, Claude Code, GitHub Copilot, Gemini CLI, Windsurf, Cline, OpenCode, Mimo Code, Hermes)
```
**After**
```markdown
- **Concrete adapters** (Cursor, Codex, Claude Code, GitHub Copilot, Gemini CLI, Windsurf, Cline, OpenCode, Mimo Code, Hermes, Junie, Kilo Code)
```
(also add a short Kilo sentence after the Hermes one: project skills under `.kilo/skills/`, MCP in `.kilo/kilo.json` key `mcp`, agent ignore `.kilocodeignore`, entry block in root `AGENTS.md`.)

### `README.md` — adapter table
**Before**
```markdown
| JetBrains Junie (`junie`) | `.junie/skills/` | `.junie/mcp/mcp.json` | `.aiignore` | `AGENTS.md` | `.junie/` |
```
**After**
```markdown
| JetBrains Junie (`junie`) | `.junie/skills/` | `.junie/mcp/mcp.json` | `.aiignore` | `AGENTS.md` | `.junie/` |
| Kilo Code (`kilo-code`) | `.kilo/skills/` | `.kilo/kilo.json` | `.kilocodeignore` | `AGENTS.md` | `.kilo/`, `.kilocode/`, `kilo.json`, `kilo.jsonc` |
```

## Additional actions
Run `uv run pytest tests/ide -q` — all green. Do not edit overview/subtask files beyond `Status: Done`.
