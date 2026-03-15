# Frontend Development Guidelines

> Best practices for frontend development in this project.

---

## Overview

Current repository status (as of 2026-03-14):

- There is **no browser frontend codebase** yet (`*.tsx`, `*.jsx`, `*.vue` are absent).
- UI output is currently delivered through:
- Terminal rendering in `xiaohongshu-cli/xhs_cli/formatter_renderers.py`
- Structured JSON/YAML envelope output in `xiaohongshu-cli/xhs_cli/formatter_utils.py`
- Markdown-based skill documents under `ohmyxhs/` and `.agents/skills/`

This directory is now filled with a **"N/A baseline + future entry constraints"** model:

- Document what is true today (no frontend app).
- Define mandatory guardrails when frontend code is introduced.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Completed (N/A baseline) |
| [Component Guidelines](./component-guidelines.md) | Component patterns, props, composition | Completed (N/A baseline) |
| [Hook Guidelines](./hook-guidelines.md) | Custom hooks, data fetching patterns | Completed (N/A baseline) |
| [State Management](./state-management.md) | Local state, global state, server state | Completed (N/A baseline) |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Completed (N/A baseline) |
| [Type Safety](./type-safety.md) | Type patterns, validation | Completed (N/A baseline) |

---

## Pre-Frontend Checklist

Before adding any browser UI package, update this directory in the same PR and include:

1. Chosen frontend stack (React/Vue/Svelte/etc.)
2. Actual directory layout and routing pattern
3. State management strategy and data fetching library
4. Type and runtime validation strategy
5. Test and lint commands integrated into project DoD

Until then, these files should be treated as operational constraints for "no frontend yet".

---

**Language**: English preferred; Chinese is acceptable when matching existing project documentation.
