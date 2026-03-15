# Directory Structure

> How frontend code is organized in this project.

---

## Overview

This workspace currently has **no browser frontend source tree**.

Evidence:

- No `*.tsx` / `*.jsx` / `*.vue` files in repository scan.
- Main deliverables are Python backend modules (`xiaohongshu-cli/`, `xhs-agent/`) and Markdown skills (`ohmyxhs/`).
- "Presentation layer" today is terminal rendering (`xhs_cli/formatter_renderers.py`), not web UI.

---

## Directory Layout

```
# Current reality (2026-03-14)
C:/study/AGI/xhs/
├── xiaohongshu-cli/         # Python CLI package
│   └── xhs_cli/
│       ├── commands/        # CLI command layer
│       ├── formatter_*.py   # terminal presentation + structured output
│       └── ...
├── xhs-agent/               # Python data pipeline package
│   └── xhs_agent/
│       ├── pipelines/
│       ├── storage/
│       └── ...
└── ohmyxhs/                 # Markdown skill assets
```

---

## Module Organization

Because there is no frontend app yet, UI-related responsibilities are split as:

1. Terminal rendering: `xiaohongshu-cli/xhs_cli/formatter_renderers.py`
2. Output schema/envelope: `xiaohongshu-cli/xhs_cli/formatter_utils.py`, `xiaohongshu-cli/SCHEMA.md`
3. CLI orchestration: `xiaohongshu-cli/xhs_cli/commands/*.py`

If a web frontend is introduced, create a dedicated app root first (example: `apps/web/`), then enforce:

1. Feature-first modules under `src/features/*`
2. Shared UI and utilities under `src/shared/*`
3. API client and boundary models under `src/api/*`
4. Test files colocated with implementation (`*.test.ts(x)`)

---

## Naming Conventions

Current naming conventions in UI-adjacent code:

- Python module files: `snake_case` (e.g., `formatter_renderers.py`)
- Render helpers: `render_*` (e.g., `render_search_results`)
- Data normalization: `normalize_*` (e.g., `normalize_note`)

Future frontend naming baseline (if introduced):

1. Components: `PascalCase.tsx`
2. Hooks: `useXxx.ts`
3. Feature folders: `kebab-case`
4. No mixed-case import path aliases

---

## Examples

Current repository examples:

1. `xiaohongshu-cli/xhs_cli/formatter_renderers.py` - terminal UI rendering functions
2. `xiaohongshu-cli/xhs_cli/formatter_normalizers.py` - view-model normalization before rendering
3. `xiaohongshu-cli/xhs_cli/commands/reading.py` - command-level orchestration and output handoff
