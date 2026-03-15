# xhs-agent Agent Guide

## Scope
- This file applies to `xhs-agent/` only.
- Keep changes focused on data collection pipelines, models, storage, and integration boundaries.

## Commands
- Install package (dev): `uv sync`
- Run tests: `uv run pytest -v`
- Run a specific test file: `uv run pytest tests/test_imports.py -v`

## Project Conventions
- Keep `xhs_agent/types.py` models and pipeline output fields consistent.
- Prefer root-cause fixes in collectors and transformers instead of patching call sites.
- Validate external payloads at boundaries before persisting to storage.
- Do not hardcode cookies, tokens, or environment-specific secrets.
- Python environment/dependency/command execution defaults to `uv` (`uv sync`, `uv run ...`).

## Debug-First
- Avoid silent downgrade paths that hide upstream issues.
- Keep failures visible through clear exceptions and test assertions.
- For pipeline fixes, verify both success path and failure path.

## Definition of Done
- Relevant tests under `tests/` pass for touched modules.
- Behavior changes are covered by tests or a reproducible command/script.
- Delivery includes file list, validation results, and known limitations.
