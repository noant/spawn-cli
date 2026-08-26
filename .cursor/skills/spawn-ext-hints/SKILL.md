---
name: spawn-ext-hints
description: Add optional hints.global / hints.local in config.yaml — plain-text agent reminders merged like global reads vs pack-local skills.
---


Goal: add short methodology reminders Spawn injects beside reads and skills — without replacing `globalRead` / `localRead` / skill `required-read`.

1. Add optional top-level **`hints`** with **`global`** and/or **`local`**, each a **YAML list of strings**. Content is **plain text only** (no pointers into other files).
2. **`global`**: included in **`spawn/navigation.yaml`** on this pack’s **`read-required` → `- ext:`** as **`hints`**, echoed into **every rendered skill** (each pack’s `hints.global`, in installed-extension order — same breadth idea as merged global mandatory reads), and merged into **`AGENTS.md`** / entry rollup together with maintainer hints.
3. **`local`**: appended only when rendering skills **owned by this pack**, after globals for that lineage; **not** written under the navigation ext **`hints`** block; **not** folded into **`AGENTS.md`**.
4. Expect **strip + dedupe by exact string** (first occurrence wins). Long lines may emit **`SpawnWarning`**; **`spawn/navigation.yaml`** may **truncate past 512 Unicode codepoints** per string; rendered skill **Hints** blocks may truncate total payload; **`AGENTS.md`** keeps full text but may warn on same thresholds — keep entries terse.
5. Use hints for durable one-liners (conventions, “always run X before Y”). Prefer real specs as **`files:`** entries with **`globalRead`** / **`localRead`** or skill **`required-read`** when the agent must load a document body.
6. **Version:** If hint text or which strings are global vs local changes observable behavior for consumers, **prompt** the author to bump **`version`** via **`spawn-ext-increment-version`** before release.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spawn-ext-guide/ai/core.md` - Machine baseline — terms, extsrc tree rules, static vs artifact, name and uniqueness, install outputs.
- `spawn-ext-guide/ai/config-yaml.md` - Machine schema for config.yaml — keys, files/folders/skills modes, reads, ignores, setup, annotated example.
- `spawn-ext-guide/user-guide.md` - Human-readable standalone guide — narrative for all authoring topics.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spawn-ext-guide/ai/skill-sources.md` - Machine rules for extsrc/skills/*.md — frontmatter, name/description resolution, rendered skill shape, example.
- `spawn-ext-guide/ai/mcp-json.md` - Machine schema for extsrc/mcp/windows.json, linux.json, macos.json — servers, OS selection, aligned name sets, transport, spawn_stdio_proxy (stdio IDE proxy), env, capabilities, validation against check, JSON examples.
- `spawn-ext-guide/ai/cli.md` - Machine CLI reference — spawn init/extension/build commands, extensions.yaml bundle shape, authoring checklist.
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
