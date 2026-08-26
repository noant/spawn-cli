---
name: spawn-ext-verify
description: Validate extension layout with Spawn CLI and smoke-test install in a disposable target.
---

Goal: ship only packs that pass strict validation and install cleanly.

1. From extension source root: **`spawn extension check . --strict`** — resolve missing skills, undeclared files under `extsrc/files/`, descriptions for non-no read flags, invalid or mismatched **`extsrc/mcp/*.json`** (including stray obsolete **`extsrc/mcp.json`**), missing setup scripts.
2. In a throwaway clone or empty repo: **`spawn init`**, then **`spawn extension add <path-or-url-to-your-extension-source>`** (match consumer workflow).
3. Confirm materialized paths under **`files:`** exist as expected; confirm **`artifact`** paths are not overwritten on a repeat add/update where applicable.
4. If **`healthcheck`** is configured: **`spawn extension healthcheck <name>`** from the target.
5. Document distribution: plain repo URL/path, zip, or entry in an **`extensions.yaml`** bundle for **`spawn build install`**.
6. **Version:** If this session changed **`config.yaml`**, skills, **`extsrc/files/`** layout, or **`extsrc/mcp/*.json`** in a user-visible way, **prompt** the author to bump **`version`** with **`spawn-ext-increment-version`** before tagging or releasing — unless they confirm it was docs-only typos with no behavioral impact.
