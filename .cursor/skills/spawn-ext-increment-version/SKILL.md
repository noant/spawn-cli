---
name: spawn-ext-increment-version
description: Bump extension version in extsrc/config.yaml for releases (semver-oriented guidance).
---


Goal: update **`version`** at the top level of **`extsrc/config.yaml`** before publishing or tagging so consumers and `spawn extension update` flows see a monotonic, intentional change.

1. Open **`extsrc/config.yaml`** and locate **`version`** (required string; compared **as a string** on extension update — ordering follows Spawn/tooling string rules, so prefer **semantic versioning** `MAJOR.MINOR.PATCH` for predictable ordering).
2. Choose bump level:
   - **PATCH** (`1.0.0` → `1.0.1`): fixes, docs-only template tweaks that do not change behavior contracts.
   - **MINOR** (`1.0.1` → `1.1.0`): backward-compatible additions (new optional files, new skills, stricter defaults that remain compatible).
   - **MAJOR** (`1.1.0` → `2.0.0`): breaking changes (removed paths, renamed skills, changed `name`, incompatible template or read semantics).
3. Edit **`version`** to the new value only — keep **`schema`**, **`name`**, and **`version`** consistent with prior releases (**`name`** MUST stay stable across releases unless you intentionally ship a new extension id).
4. If the repo keeps a **changelog**, add an entry for this version in that file (optional; not part of Spawn manifest).
5. Run **`spawn extension check . --strict`** from the extension source root.

Do **not** bump **`schema`** unless you migrate to a new Spawn **`config.yaml`** format version documented by Spawn.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spawn-ext-guide/ai/core.md` - Machine baseline — terms, extsrc tree rules, static vs artifact, name and uniqueness, install outputs.
- `spawn-ext-guide/ai/config-yaml.md` - Machine schema for config.yaml — keys, files/folders/skills modes, reads, ignores, setup, annotated example.
- `spawn-ext-guide/ai/cli.md` - Machine CLI reference — spawn init/extension/build commands, extensions.yaml bundle shape, authoring checklist.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spawn-ext-guide/ai/skill-sources.md` - Machine rules for extsrc/skills/*.md — frontmatter, name/description resolution, rendered skill shape, example.
- `spawn-ext-guide/ai/mcp-json.md` - Machine schema for extsrc/mcp/windows.json, linux.json, macos.json — servers, OS selection, aligned name sets, transport, spawn_stdio_proxy (stdio IDE proxy), env, capabilities, validation against check, JSON examples.
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
