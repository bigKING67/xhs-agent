# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

There is currently no browser frontend module in this repository.

Quality baseline for UI-facing behavior is enforced through CLI/pipeline standards:

1. Lint and static checks: `ruff` + `mypy` (`xiaohongshu-cli`)
2. Automated tests: `pytest` suites in both subprojects
3. Structured output contract stability for machine consumers
4. No hidden fallback or silent downgrade in failure paths

---

## Forbidden Patterns

1. Introducing frontend framework code without creating a dedicated frontend package and updating these docs.
2. Mixing rendering/presentation logic with transport and business logic.
3. Swallowing errors instead of mapping to explicit structured failure output.
4. Leaking secrets/tokens/cookies in logs or rendered output.
5. Breaking `SCHEMA.md` output envelope compatibility without explicit migration note.

Representative code locations:

1. `xiaohongshu-cli/xhs_cli/commands/_common.py`
2. `xiaohongshu-cli/xhs_cli/formatter_utils.py`
3. `xiaohongshu-cli/xhs_cli/error_codes.py`

---

## Required Patterns

1. Keep structured output pathway available (`--json`/`--yaml`) for any user-facing command output.
2. Reuse shared command wrappers for consistent error and auth/session behavior.
3. Keep retry/cooldown/rate-limit logic centralized in base client/collector code.
4. Keep data normalization and rendering separated.

Reference examples:

1. `xiaohongshu-cli/xhs_cli/commands/reading.py`
2. `xiaohongshu-cli/xhs_cli/formatter_normalizers.py`
3. `xhs-agent/xhs_agent/pipelines/collection/base.py`

---

## Testing Requirements

Current required checks (UI-related behavior included):

1. `cd xiaohongshu-cli && uv run ruff check .`
2. `cd xiaohongshu-cli && uv run mypy xhs_cli/`
3. `cd xiaohongshu-cli && uv run pytest tests/ -v -m "not smoke"`
4. `cd xhs-agent && pytest -v` for touched `xhs-agent` modules

When frontend app is introduced, this section must add:

1. Frontend lint command
2. Frontend typecheck command
3. Unit/component test command
4. Basic accessibility/interaction test expectations

---

## Code Review Checklist

1. Does the change preserve structured output compatibility and error-code stability?
2. Are rendering concerns separated from command transport/business logic?
3. Are failures observable (not silently swallowed)?
4. Are sensitive fields excluded from logs and output?
5. Are relevant lint/type/test commands run for touched subprojects?
6. If frontend code is newly introduced, were these frontend spec files updated in the same PR?
