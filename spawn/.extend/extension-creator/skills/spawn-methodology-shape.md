---
name: spawn-methodology-shape
description: Design methodology content layout — what lives in templates, artifacts, and agent-facing reads for a new practice.
---

Goal: before editing YAML heavily, decide what the methodology teaches and where files live under `extsrc/files/`.

1. Define audiences (human vs agent) and primary workflows; map each to concrete paths under a single namespace prefix.
2. Classify each deliverable as `static` (canonical methodology the pack maintains) vs `artifact` (per-repo living documents).
3. Choose what belongs in global navigation (`globalRead`) vs only when using this pack’s skills (`localRead`).
4. Split long specs into `extsrc/files/` and keep `extsrc/skills/*.md` as thin procedures that point to those reads.
5. Align names with uniqueness rules (prefixed skill ids, MCP server ids, path prefixes) if this pack coexists with others.
6. Implement the tree under `extsrc/files/`, then run `spawn-ext-config` and `spawn-ext-verify` workflows.
7. **Version:** If namespaces, static vs artifact split, or read surfaces change shipped methodology, **prompt** the author to bump **`version`** via **`spawn-ext-increment-version`** before consumers upgrade.
