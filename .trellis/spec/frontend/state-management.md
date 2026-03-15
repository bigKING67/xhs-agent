# State Management

> How state is managed in this project.

---

## Overview

No browser frontend state library is used because no frontend app exists yet.

Current repository state is managed in three non-frontend forms:

1. In-process runtime state (client/session counters, pipeline execution state)
2. Local persisted cache/config JSON files
3. Command context objects passed through Click

---

## State Categories

Current categories and examples:

1. Runtime ephemeral state  
   `xiaohongshu-cli/xhs_cli/client.py`: request delay, verification counters, retry loop state
2. Local persisted state  
   `xiaohongshu-cli/xhs_cli/cookies.py`: `cookies.json`, `token_cache.json`, `index_cache.json`
3. Pipeline/result state  
   `xhs-agent/xhs_agent/pipelines/collection/base.py`: collection stats and error accumulation
4. Storage state  
   `xhs-agent/xhs_agent/storage/json_store.py`: JSON snapshots for notes, celebs, analysis, strategies

---

## When to Use Global State

Current rule set:

1. Use function parameters/context objects first.
2. Promote to module-level/shared state only for immutable config constants.
3. Persist only if restart continuity is required (cookie/session/token caches, collected datasets).

Do not create implicit mutable globals for request/session control.

---

## Server State

Server state is fetched on demand from Xiaohongshu APIs and handled as follows:

1. CLI layer transforms raw responses for display/output.
2. Token and note index caches are persisted locally for command UX.
3. `xhs-agent` can persist collected entities and analysis results via storage backends.

There is no frontend query cache (e.g., React Query) at this stage.

---

## Common Mistakes

1. Reading cookie files directly instead of going through `get_cookies()` lifecycle checks.
2. Bypassing existing note/token cache helpers and duplicating cache keys.
3. Mixing storage persistence concerns into command handlers.
4. Storing sensitive data in logs or unchecked debug payloads.

If a browser frontend is added, define local/global/server/url state boundaries here with concrete examples.
