# Rule: single canonical config file for adapters

Optional. For IDE adapters that write a project-scope config file where the
agent supports variant formats (e.g. `opencode.json` vs `opencode.jsonc`).

Conventions:

1. Pick ONE canonical file and always read/write only it (precedent:
   `opencode.py` -> root `opencode.json`). Never merge variant formats
   (JSONC comments make safe merges impossible with `json`).
2. If only a variant file exists, still write the canonical file and emit a
   `SpawnWarning` naming both files.
3. If the canonical file is unparseable, raise `SpawnError` BEFORE any
   mutation (no partial writes; per `ide-adapters.md` Error And Warning Rules).
4. On removal, prune only spawn-owned keys and their empty subtrees; keep the
   file when any user content remains (paired rule:
   `spawn/rules/01-vacancy-cleanup-subtrees.md`).
5. When the tool accepts the same config in several locations (e.g. Kilo Code:
   root `kilo.json` vs `.kilo/kilo.json`), pick ONE canonical path and emit a
   `SpawnWarning` naming every other existing location that spawn does NOT
   merge — the unmanaged file may shadow or duplicate the canonical one
   (precedent: `kilo_code.py` `_load_config`, task 34).
