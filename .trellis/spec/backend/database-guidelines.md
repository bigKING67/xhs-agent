# Database Guidelines

> Database and persistence conventions for this repository.

---

## Overview

This workspace has two backend subprojects with different persistence models:

1. `xiaohongshu-cli`: **no SQL database**, only local cache/config JSON files.
2. `xhs-agent`: file-based storage backend implemented (`JSONStorage`), and storage abstraction for future backends.

There is currently no active ORM migration workflow in this repo.

---

## Project-by-Project Reality

### 1) xiaohongshu-cli

Persistence is local runtime support data, not business DB tables.

Examples:

1. `xiaohongshu-cli/xhs_cli/cookies.py`  
   Maintains cookie lifecycle and local cache files.
2. `xiaohongshu-cli/xhs_cli/note_refs.py`  
   Maintains short-index navigation cache for CLI UX.
3. `xiaohongshu-cli/xhs_cli/commands/_common.py`  
   Consumes cached/auth state through shared helpers.

Typical local files:

1. `~/.xiaohongshu-cli/cookies.json`
2. `~/.xiaohongshu-cli/token_cache.json`
3. `~/.xiaohongshu-cli/index_cache.json`

### 2) xhs-agent

Persistence is implemented through storage abstraction and JSON backend.

Examples:

1. `xhs-agent/xhs_agent/storage/base.py`  
   Defines `BaseStorage`, `StorageManager`, and `StorageContext`.
2. `xhs-agent/xhs_agent/storage/json_store.py`  
   Implements note/celebrity/analysis/strategy persistence as JSON files.
3. `xhs-agent/xhs_agent/core/orchestrator.py`  
   Uses `StorageContext("json", {"path": ...})` to persist pipeline outputs.

---

## Current Storage Pattern

### Use Abstract Storage Boundary

Always program against storage interface where possible:

1. Open storage via `StorageContext`/`StorageManager`
2. Call typed save/get methods
3. Keep persistence concerns out of pipeline orchestration logic

Do not scatter direct file writes across unrelated modules.

### Prefer Typed Models at Boundaries

`xhs-agent` uses Pydantic models (`xhs_agent/types.py`) before persistence.

Benefits:

1. Runtime validation
2. Stable schema shape
3. Safer serialization (`model_dump(mode="json")`)

### Keep CLI Caches as Operational Data

`xiaohongshu-cli` local JSON files are operational cache/config, not authoritative business records.
Use existing helpers instead of ad hoc cache file edits.

---

## Migrations and Schema Changes

There is no formal DB migration toolchain (Alembic/Flyway/etc.) in current repo state.

For persistence contract changes:

1. Update typed models and storage read/write code together.
2. Keep backward compatibility for existing local JSON when feasible.
3. Add tests for both load and save paths.
4. Document breaking changes in related README/spec files.

---

## Forbidden Patterns

1. Hardcoding secrets/tokens in persisted files under version control.
2. Bypassing storage abstractions with random path writes in business code.
3. Treating transient cache files as source-of-truth business data.
4. Introducing SQL dependencies/migrations without explicit project-level decision.

---

## Validation Checklist

When changing persistence behavior, verify at least:

1. Save path works (`save_*` methods return expected results).
2. Read path works (`get_*` methods reconstruct valid typed objects).
3. Failure path is observable (logged/raised, not silently ignored).
4. Related tests are updated:
   - `xhs-agent/tests/test_storage_stats.py`
   - `xhs-agent/tests/test_collection_transformers.py` (if model shape affected)
   - `xiaohongshu-cli/tests/test_cookies.py` (if CLI cache behavior affected)

---

## Related Guidelines

1. [`directory-structure.md`](./directory-structure.md)
2. [`error-handling.md`](./error-handling.md)
3. [`logging-guidelines.md`](./logging-guidelines.md)
4. [`quality-guidelines.md`](./quality-guidelines.md)
