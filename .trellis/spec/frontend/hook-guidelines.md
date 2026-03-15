# Hook Guidelines

> How hooks are used in this project.

---

## Overview

No React hook system exists in the current codebase.

Equivalent reusable stateful patterns today are implemented with Python helpers and context managers.

Current focus:

1. Reuse shared action wrappers for command error handling.
2. Centralize retry/rate-limit logic in collector/client base classes.
3. Avoid copy-pasting stateful flow logic across commands/pipelines.

---

## Custom Hook Patterns

Current "hook-equivalent" patterns:

1. `xiaohongshu-cli/xhs_cli/commands/_common.py::run_client_action`  
   Encapsulates auth/session refresh and retries once with refreshed cookies.
2. `xhs-agent/xhs_agent/pipelines/collection/base.py::collect_batch_async`  
   Encapsulates concurrency control + retry + skip-on-failure strategy.
3. `xhs-agent/xhs_agent/storage/base.py::StorageContext`  
   Encapsulates storage lifecycle through context manager.

Future hook rule (when frontend exists): all custom hooks must start with `use` and own one clear responsibility.

---

## Data Fetching

Current data fetching is not frontend-driven:

1. CLI runtime fetches via `XhsClient` + endpoint mixins (`xhs_cli/client.py`, `xhs_cli/client_mixins.py`).
2. Batch pipelines fetch via aggregator classes (`xhs_agent/pipelines/collection/*`).
3. Retry/backoff is part of shared lower-level utilities, not command-level duplication.

Do not introduce parallel ad hoc fetching wrappers when existing shared flows can be reused.

---

## Naming Conventions

Current reusable logic naming:

1. Wrapper-style helpers: `run_*`, `handle_*`, `get_*`, `collect_*`
2. Internal methods: leading underscore for non-public behavior (`_collect_with_retry`)
3. Context managers: `*Context` suffix (e.g., `StorageContext`)

Future frontend naming baseline:

1. `useXxx` for hooks
2. `useFeatureAction` for side-effect orchestration hooks
3. No anonymous default-export hook modules

---

## Common Mistakes

1. Reimplementing retry/session handling instead of using `_common.py` wrappers.
2. Duplicating concurrency controls across collectors rather than reusing base collector logic.
3. Mixing side effects into render/output functions.
4. Introducing hidden mutable globals for flow state.

If frontend hooks appear later, replace this section with concrete hook pitfalls from real code.
