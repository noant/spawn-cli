# 1: Project metadata

## Goal
Create Python project metadata for an installable CLI package.

## Approach
Add `pyproject.toml` with setuptools build configuration, package discovery for `src/`, project metadata, the `spawn` console script, and pytest configuration.

## Affected files
- `pyproject.toml`

## Code examples
```toml
[project.scripts]
spawn = "spawn_cli.cli:main"
```
