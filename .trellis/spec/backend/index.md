# Backend Development Guidelines

> Best practices for backend development in this project.

---

## Overview

This repository is a multi-project Python workspace, primarily:

1. `xiaohongshu-cli` (CLI + API client)
2. `xhs-agent` (collection/analysis/storage/strategy pipeline)

This directory documents backend conventions based on current code reality.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Completed |
| [Database Guidelines](./database-guidelines.md) | ORM patterns, queries, migrations | Completed |
| [Error Handling](./error-handling.md) | Error types, handling strategies | Completed |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Completed |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, log levels | Completed |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals)
2. Include **code examples** from your codebase
3. List **forbidden patterns** and why
4. Add **common mistakes** your team has made

The goal is to help AI assistants and new team members understand how YOUR project works.

---

**Language**: English preferred; Chinese is acceptable when matching existing project documentation.
