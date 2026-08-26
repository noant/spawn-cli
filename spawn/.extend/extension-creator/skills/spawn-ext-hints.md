---
name: spawn-ext-hints
description: Declare optional hints.global / hints.local in config.yaml — plain-text reminders merged into navigation, rendered skills, and AGENTS rollup.
---

Goal: add short methodology reminders Spawn injects beside reads and skills — without replacing `globalRead` / `localRead` / skill `required-read`.

1. Add optional top-level **`hints`** with **`global`** and/or **`local`**, each a **YAML list of strings**. Content is **plain text only** (no pointers into other files).
2. **`global`**: included in **`spawn/navigation.yaml`** on this pack’s **`read-required` → `- ext:`** as **`hints`**, echoed into **every rendered skill** (each pack’s `hints.global`, in installed-extension order — same breadth idea as merged global mandatory reads), and merged into **`AGENTS.md`** / entry rollup together with maintainer hints.
3. **`local`**: appended only when rendering skills **owned by this pack**, after globals for that lineage; **not** written under the navigation ext **`hints`** block; **not** folded into **`AGENTS.md`**.
4. Expect **strip + dedupe by exact string** (first occurrence wins). Long lines may emit **`SpawnWarning`**; **`spawn/navigation.yaml`** may **truncate past 512 Unicode codepoints** per string; rendered skill **Hints** blocks may truncate total payload; **`AGENTS.md`** keeps full text but may warn on same thresholds — keep entries terse.
5. Use hints for durable one-liners (conventions, “always run X before Y”). Prefer real specs as **`files:`** entries with **`globalRead`** / **`localRead`** or skill **`required-read`** when the agent must load a document body.
6. **Version:** If hint text or which strings are global vs local changes observable behavior for consumers, **prompt** the author to bump **`version`** via **`spawn-ext-increment-version`** before release.
