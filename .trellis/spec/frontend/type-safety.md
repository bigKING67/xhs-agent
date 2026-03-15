# Type Safety

> Type safety patterns in this project.

---

## Overview

Current codebase type safety is Python-first (not TypeScript-first).

Primary mechanisms:

1. Static typing via `mypy` in `xiaohongshu-cli`
2. Runtime validation + schema modeling via `pydantic` in `xhs-agent`
3. Structured output contracts via `SCHEMA.md` and formatter envelope functions

No frontend TS type system exists yet.

---

## Type Organization

Current type organization examples:

1. Domain exceptions and stable error-code mapping:
- `xiaohongshu-cli/xhs_cli/exceptions.py`
- `xiaohongshu-cli/xhs_cli/error_codes.py`
2. Core data contracts for collection/analysis/strategy:
- `xhs-agent/xhs_agent/types.py`
3. CLI command interfaces and action wrappers:
- `xiaohongshu-cli/xhs_cli/commands/_common.py`

Guideline:

1. Put shared contracts in dedicated modules (`types.py`, `exceptions.py`).
2. Avoid ad hoc untyped dict contracts spread across many files.

---

## Validation

Current runtime validation strategy:

1. `pydantic` models validate input/output entities in `xhs-agent`.
2. CLI error paths map exceptions to stable machine-readable error codes.
3. Structured output builders must preserve envelope schema shape (`ok`, `schema_version`, `data/error`).

Future frontend note:

When TS frontend is introduced, add runtime validation (e.g., Zod) at API boundaries and sync with backend contracts.

---

## Common Patterns

Current common patterns:

1. Use `from __future__ import annotations` for forward references.
2. Use precise exception classes instead of broad `Exception` handling in command/service boundaries.
3. Use typed models (`BaseModel`) for cross-layer payloads instead of free-form nested dicts where possible.
4. Keep error contract stable through centralized mapping (`error_code_for_exception`).

---

## Forbidden Patterns

1. Untyped function signatures for public/internal boundary functions.
2. Raw `except Exception: pass` that erases type/error semantics.
3. Returning inconsistent error payload shapes from command handlers.
4. Hardcoding dynamic payload keys without normalization/mapping layer.
5. Introducing TypeScript-only conventions before an actual TS frontend package exists.
