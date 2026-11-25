# 35: Navigation rules accept non-spawn/rules paths with round-trip YAML

## Source seed
- Path: none

## Status
- [V] Research [glm-5.4]
- [ ] User research review
- [V] Spec drafting [glm-5.3]
- [V] Spec self-review [glm-5.3 + kimi-k3.1-pro]
- [V] Spec review
- [V] Code implementation [glm-5.3]
- [V] Code self-review [glm-5.3 + kimi-k3.1-pro]
- [ ] Code review / debugging
- [V] Design document update [glm-5.3]

## Goal
Allow spawn/navigation.yaml rules rows to reference any existing repo-relative file (e.g. spec/design/*.md), pruning only missing files, and preserve YAML comments via round-trip mode.

## Motivation
Design docs must be indexed directly in spawn/navigation.yaml (spectask 18) so they render into AGENTS.md; today save_rules_navigation prunes any path outside spawn/rules/.

## Invasiveness level
medium-invasive

## Review models
- Research review: cross-review: glm-5.3, kimi-k3.1-pro
- Spec review: cross-review: glm-5.3, kimi-k3.1-pro
- Code review: cross-review: glm-5.3, kimi-k3.1-pro
- fallback: deepseek-v4-pro

## Run mode
auto

## Research summary
- save_rules_navigation: src/spawn_cli/core/low_level.py:1129-1267; prune checks at 1196 (prune_read_required_rules) and 1243 (prune_contextual_rules) require `rk in paths_on_disk and file-exists`.
- paths_on_disk (1136-1141) still needed for auto-add (1173-1175).
- yaml_io.py load_yaml/save_yaml use YAML(typ="safe") — comments lost; reference rt implementation save_extension_navigation (1079-1125).
- Readers (navigation_refs_for_agents:305, high_level:199) use safe load of the serialized file — rt dump is compatible.
- Tests: tests/core/test_low_level.py 644-1041; no non-rules-path coverage; comment test only for save_extension_navigation (1015).

## Design overview
- Affected modules: spawn_cli.core.low_level
- Files & symbols: save_rules_navigation, prune_read_required_rules, prune_contextual_rules, _ensure_navigation_root_key_order
- Data flow changes: navigation.yaml rules rows may carry any repo-relative path; comments preserved across refresh
- Integration points: AGENTS.md rendering (navigation_refs_for_agents), spectask 18 migration

## Before → After
### Before
- Rules rows outside spawn/rules/ pruned with "Removed missing rule path" warning even when the file exists.
- save_rules_navigation round-trips via safe YAML: comments dropped.
### After
- Rules rows kept when the file exists anywhere inside the repo root (path containment enforced); pruned with warning only when missing.
- Comments preserved (rt load/dump, no list() copies of sections).

## Details
- Path containment: reject absolute paths and paths escaping target_root before the existence check (resolve and verify containment) — reviewers flagged security concern.
- Call _ensure_navigation_root_key_order(raw) before dump (parity with save_extension_navigation).
- Keep auto-add of new spawn/rules/ files unchanged.

## Execution Scheme
Suggested coordinator model: glm-5.3
- Phase 1 (sequential): step 1-prune-and-roundtrip → step 2-tests
