linked task: none

## Idea (informal)

Introduce a **settings file** (YAML) that declares **directed links between Spawn extensions** (methodology packs), e.g. `depends-on` / `extends` / `requires-extension` edges: **from consumer extension → provider extension**.

**Coherent methodology chain:** the graph encodes how one pack builds on another so navigation and agent reads stay aligned across extensions, not only within a single `config.yaml`.

**Read propagation:** for each edge **A → B**, paths that extension **B** exposes with **`localRead: required`** (and possibly **`localRead: auto`** — to decide in spec) should **surface as mandatory reads** for work scoped to **A** (or merge into the same `read-required` / skill injection rules that today only consider files inside one extension). Effectively: **linked extension’s `localRead` becomes part of the dependent extension’s required reading surface**, without duplicating file entries in A’s `config.yaml`.

## Design questions (for `spectask-create`)

- Where does the YAML live: `spawn/` root, per-extension slice under `spawn/.extend/{name}/`, or both (manifest + merge)?
- Exact semantics: only `localRead: required`, or also `auto` as contextual for A?
- Cycles, multiple parents, and ordering when B and C both link from A.
- Interaction with existing merge rules (`read-required` wins over contextual; dedup across extensions).
- Strict mode vs opt-in: only extensions that declare an edge get propagation, or global registry.

When you promote this seed, run **`spectask-create`**; **Step 1** and **Step 7** item **4** (seed ↔ overview linking) apply there.
