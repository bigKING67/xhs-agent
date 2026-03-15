<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

Use the `/trellis:start` command when starting a new session to:
- Initialize your developer identity
- Understand current project context
- Read relevant guidelines

Use `@/.trellis/` to learn:
- Development workflow (`workflow.md`)
- Project structure guidelines (`spec/`)
- Developer workspace (`workspace/`)

Keep this managed block so 'trellis update' can refresh the instructions.

<!-- TRELLIS:END -->

<!-- CODEX-BASELINE:START -->
## Codex Baseline

### Scope
- This repository is a multi-project workspace for Xiaohongshu tooling and AI skills.
- Keep changes scoped to the requested subproject; avoid cross-project refactors unless requested.

### Repository Map
- `xiaohongshu-cli/`: production CLI package (`xhs_cli/`) and tests (git submodule, upstream: `jackwener/xiaohongshu-cli`).
- `xhs-agent/`: data collection and analysis package (`xhs_agent/`) and tests.
- `ohmyxhs/`: strategy skill assets and references.
- `.trellis/`: workflow, task, and spec orchestration docs.
- `.agents/skills/`: local reusable skills and playbooks.

### Task Input Template
Use this template before implementation when requirements are fuzzy or complex:
- Goal: target behavior change.
- Context: related files, directories, and failing commands.
- Constraints: architecture, security, and compatibility boundaries.
- Done when: observable behavior and verification commands.

### Commands
- `xiaohongshu-cli` install: `cd xiaohongshu-cli && uv sync`
- `xiaohongshu-cli` run: `cd xiaohongshu-cli && uv run xhs search "keyword" --yaml`
- `xiaohongshu-cli` lint: `cd xiaohongshu-cli && uv run ruff check .`
- `xiaohongshu-cli` type-check: `cd xiaohongshu-cli && uv run mypy xhs_cli/`
- `xiaohongshu-cli` tests (default): `cd xiaohongshu-cli && uv run pytest tests/ -v -m "not smoke"`
- `xiaohongshu-cli` smoke tests: `cd xiaohongshu-cli && uv run pytest tests/ -v -m smoke`
- `xiaohongshu-cli` sync upstream: `git submodule update --init --recursive && cd xiaohongshu-cli && git checkout main && git pull --ff-only origin main`
- `xhs-agent` install dev deps: `cd xhs-agent && uv sync`
- `xhs-agent` tests: `cd xhs-agent && uv run pytest -v`
- `codex` instruction smoke: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/codex-smoke.ps1 -Profile fast -Subdir xiaohongshu-cli`
- pre-delivery checklist: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/codex-checklist.ps1 -Target all`

### Engineering Conventions
- Fix root causes, not only symptoms.
- Keep patches minimal and focused; avoid unrelated churn.
- Preserve observability and avoid silent fallback that hides failures.
- Add or update tests when behavior changes.
- Use `uv` as the default Python workflow for env/deps/run (avoid `pip`/manual `venv` unless explicitly requested).
- Keep Python dependency metadata reproducible: maintain `pyproject.toml` and commit `uv.lock` after dependency changes.
- For complex work, plan first (Plan mode or `PLANS.md`) before editing.
- Before final delivery, run a self-review using `code_review.md`.

### Safety Constraints
- Never hardcode secrets or tokens in source files.
- Do not modify any `.trellis/*` files unless the user explicitly asks for it.
- Confirm before destructive operations (`rm`, force-push, history rewrite, or bulk replace across many files).
- Prefer non-interactive and auditable commands.
- Validate untrusted external input at system boundaries.

### Definition of Done
- Relevant checks for touched modules pass (tests, lint, and type-check where available).
- Behavior change is verifiable with concrete commands.
- Diff is reviewed for unintended changes.
- Delivery includes summary, affected files, validation results, and risks or unknowns.
<!-- CODEX-BASELINE:END -->
