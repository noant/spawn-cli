---
name: spawn-ext-increment-version
description: Bump the extension version string in extsrc/config.yaml for a release or compatibility signal.
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
