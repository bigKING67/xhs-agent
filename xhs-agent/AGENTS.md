# xhs-agent Agent Guide

## Scope
- This file applies to `xhs-agent/` only.
- Keep changes focused on data collection pipelines, models, storage, and integration boundaries.

## Commands
- Install package (dev): `uv sync`
- Run tests: `uv run pytest -v`
- Run a specific test file: `uv run pytest tests/test_imports.py -v`
- Sync upstream `xiaohongshu-cli` (from repo root): `git submodule update --init --recursive && cd xiaohongshu-cli && git checkout main && git pull --ff-only origin main`
- Sync upstream via script (recommended, from repo root): `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-xiaohongshu-cli.ps1 -AutoStash`
- Analyze upstream impact before patching (from repo root): `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/analyze-xiaohongshu-cli-update.ps1`
- Sync + analyze + export report (recommended CI-like flow): `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-xiaohongshu-cli.ps1 -AutoStash -AnalysisOutputFile xhs-agent/data/upstream-analysis-latest.md`

## Project Conventions
- Keep `xhs_agent/types.py` models and pipeline output fields consistent.
- Prefer root-cause fixes in collectors and transformers instead of patching call sites.
- Validate external payloads at boundaries before persisting to storage.
- Do not hardcode cookies, tokens, or environment-specific secrets.
- Python environment/dependency/command execution defaults to `uv` (`uv sync`, `uv run ...`).
- Keep dependency config reproducible: update `pyproject.toml` and commit refreshed `uv.lock` whenever dependencies change.

## Upstream Update Playbook (`xiaohongshu-cli`)
- Goal: update upstream safely without losing local WIP in `xiaohongshu-cli/`.
- Preferred one-command flow:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-xiaohongshu-cli.ps1 -AutoStash`
  - Optional report file: append `-AnalysisOutputFile xhs-agent/data/upstream-analysis-latest.md`
- If submodule has local changes, stash before pull:
  - `cd ../xiaohongshu-cli`
  - `git stash push -u -m "temp-before-upstream-sync"`
  - `git pull --ff-only origin main`
  - `git stash apply` (resolve conflicts, prefer local WIP unless explicitly replacing)
- If submodule is clean, fast path:
  - `cd ../xiaohongshu-cli && git checkout main && git pull --ff-only origin main`
- After update, go back to root and decide whether to record pointer bump:
  - `cd .. && git add xiaohongshu-cli && git commit -m "chore: bump xiaohongshu-cli submodule"`

## Post-Update Actions (Required)
- Always run compatibility checks after upstream sync:
  - `cd ../xiaohongshu-cli && uv sync`
  - `cd ../xhs-agent && uv sync`
  - `uv run pytest -v`
- On Windows terminals using GBK code page, run CLI help checks with UTF-8 mode:
  - PowerShell: `$env:PYTHONUTF8='1'; uv run xhs --help`
- If failures appear, prioritize adapter boundary:
  - `xhs_agent/integrations/xhs_factory.py`
  - `xhs_agent/pipelines/collection/notes.py`
  - `xhs_agent/pipelines/collection/comments.py`
  - `xhs_agent/pipelines/collection/celebrity.py`
  - `tests/test_collectors_integration.py`

## When To Adjust Secondary Development
- Usually no code change needed in `xhs-agent` when upstream changes are only docs/CI/lockfile.
- Re-evaluate and patch `xhs-agent` when upstream touches API behavior or payload shape, especially:
  - `xhs_cli/client.py`
  - `xhs_cli/client_mixins.py`
  - `xhs_cli/commands/reading.py`
  - structured output/schema related files
- If upstream introduces a breaking dependency/version floor, update `xhs-agent` dependency constraints and refresh `uv.lock`.
- Use `scripts/analyze-xiaohongshu-cli-update.ps1` to classify risk first, then decide whether patch is required.

## Debug-First
- Avoid silent downgrade paths that hide upstream issues.
- Keep failures visible through clear exceptions and test assertions.
- For pipeline fixes, verify both success path and failure path.

## Definition of Done
- Relevant tests under `tests/` pass for touched modules.
- Behavior changes are covered by tests or a reproducible command/script.
- Delivery includes file list, validation results, and known limitations.
