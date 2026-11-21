# 10: Adapt publish.py for spawn-cli

## Source seed
- Path: none

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal
Align `scripts/publish.py` with the spawn-cli repository (naming, documentation, and user-facing messages) while keeping the existing uv build, patch bump, dist cleanup, and PyPI publish flow.

## Design overview
- Affected modules: `scripts/publish.py` only (maintainers’ tooling; not part of the installed `spawn_cli` package).
- Data flow changes: None; still reads/writes root `pyproject.toml`, cleans `dist/`, runs `uv build` and `uv publish` with `UV_PUBLISH_TOKEN` for the subprocess.
- Integration points: Root `pyproject.toml` (`[project]` / `version`), `uv` on PATH, PyPI token via environment or `--token`.

## Before → After
### Before
- Docstring and help text refer to `spectask_publish_pypi_token` and “spectask”-style wording copied from another project.
- Log/error prefix is generic `publish:` (acceptable but not package-scoped).

### After
- Preferred token environment variable: `SPAWN_CLI_PYPI_TOKEN` (CLI `--token` still overrides when both are set).
- Docstring and argparse help describe spawn-cli and the new env var; examples in the docstring updated.
- Stderr messages use a consistent prefix such as `spawn-cli publish:` so grepping logs is unambiguous.
- No change to semver bump rules: still increment the last dot-separated segment of `[project].version` in the root `[project]` table (must be decimal digits in the last segment), compatible with current `pyproject.toml` (`version = "0.1.0"`).

## Details
- Keep `UV_PUBLISH_TOKEN` as the variable passed into the `uv publish` subprocess (per uv’s contract).
- `pyproject.toml` layout: setuptools backend, `[project]` at repo root — existing `_project_root_version_line_index` and `_VERSION_LINE` logic remains valid.
- Out of scope for this task: adding minor/major bump flags, TestPyPI profiles, or CI integration; those can be separate tasks if needed.
