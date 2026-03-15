# Component Guidelines

> How components are built in this project.

---

## Overview

There is no React/Vue component system in this repository at the moment.

The closest "component-like" units are terminal render functions and schema-first output payloads.

Current guidance is therefore:

1. Follow existing presentation separation in CLI modules.
2. Do not invent pseudo-frontend abstractions without an actual frontend package.
3. If frontend is added, this file must be rewritten with concrete component standards in that same PR.

---

## Component Structure

Current UI-equivalent pipeline in `xiaohongshu-cli`:

1. Fetch raw data via client method
2. Normalize data (`formatter_normalizers.py`)
3. Render data (`formatter_renderers.py`) or emit structured payload (`formatter_utils.py`)

Recommended separation:

- "Container role": command handlers in `xhs_cli/commands/*.py`
- "Presentational role": `render_*` functions
- "View-model mapping": `normalize_*` functions

---

## Props Conventions

For terminal renderers, treat function arguments as "props":

1. Input should be normalized dict/list, not raw API payload whenever possible.
2. Keep renderer parameters explicit; avoid hidden global state.
3. For structured output, use envelope builders (`success_payload`, `error_payload`) instead of ad hoc dict assembly.

Representative examples:

1. `xiaohongshu-cli/xhs_cli/formatter_utils.py`
2. `xiaohongshu-cli/xhs_cli/formatter_normalizers.py`
3. `xiaohongshu-cli/xhs_cli/commands/_common.py`

---

## Styling Patterns

Current styling surface is terminal text via Rich:

1. Use Rich renderers for human-readable output.
2. Use JSON/YAML schema envelopes for machine-readable output.
3. Keep style concerns in renderer layer only (no ANSI/style tokens in command/business code).

---

## Accessibility

Current accessibility constraints (CLI context):

1. Any command output must have a machine-readable alternative (`--json` or `--yaml`).
2. Default output mode should remain deterministic in non-TTY contexts.
3. Avoid color-only semantics for critical errors; ensure message text is self-sufficient.

---

## Common Mistakes

1. Mixing API calls directly into rendering code.
2. Skipping normalization and rendering raw heterogeneous payloads.
3. Printing ad hoc errors instead of unified error envelope pathways.
4. Treating terminal rendering functions as business logic containers.

If a browser frontend is introduced, add real component anti-patterns (prop drilling, unstable keys, etc.) here.
