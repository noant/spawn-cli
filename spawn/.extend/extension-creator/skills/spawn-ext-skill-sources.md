---
name: spawn-ext-skill-sources
description: Author extsrc/skills/*.md and register them in config.yaml with merges and required reads.
---

Goal: add or change agent skills shipped with the extension.

1. Add `extsrc/skills/<skill-key>.md` (UTF-8 Markdown). Filename must match the key under `skills:` when declared.
2. Prefer short procedural bodies; long reference belongs under `extsrc/files/` and is linked via `localRead`/`globalRead` or per-skill `required-read`.
3. Optional YAML frontmatter with `name` and/or `description`; otherwise set them under `skills:` in `config.yaml` (config overrides frontmatter where both apply per resolution rules).
4. Under `skills:` list `required-read` target paths only when they are mandatory for that skill beyond merged global/local rules; avoid pointless duplication.
5. After normalization, skill display names must remain unique across all extensions installed in one target — use a stable prefix.
6. Run `spawn extension check . --strict` after adding or renaming skill files.
7. **Version:** Adding, removing, or materially changing skills or their **`required-read`** affects consumers — **prompt** the author to bump **`version`** via **`spawn-ext-increment-version`** before release (unless the change is typo-only text with no behavior impact).
