# Database Guidelines

> Database patterns and conventions for this project.

---

## Status: N/A

**xiaohongshu-cli is a pure API client with NO database operations.**

This project:
- ✅ Makes HTTP calls to Xiaohongshu (XHS) API
- ✅ Stores configuration locally in JSON files (`~/.xiaohongshu-cli/`)
- ❌ Does NOT use any ORM (SQLAlchemy, Django ORM, etc.)
- ❌ Does NOT use any database (PostgreSQL, MySQL, SQLite, etc.)
- ❌ Does NOT have migrations

---

## Project Scope

### What This Project Does

- **API Client** — Reverse-engineered Xiaohongshu API calls
- **CLI Tool** — Command-line interface for interacting with XHS
- **Local Config Storage** — JSON files for cookies, tokens, caches

### What This Project Does NOT Do

- Store user data in database
- Persist application state beyond process lifetime
- Manage relational data structures
- Require schema management or migrations

---

## Local Storage (JSON-based)

If you need to understand how data is stored locally, see:

**Location**: `xhs_cli/cookies.py`

**Files**:
- `~/.xiaohongshu-cli/cookies.json` — User cookies + TTL
- `~/.xiaohongshu-cli/token_cache.json` — xsec_token cache
- `~/.xiaohongshu-cli/index_cache.json` — Note index cache (for CLI shortcuts)

**Operations** (read/write JSON):
```python
import json
from pathlib import Path

def load_cookies() -> dict:
    """Load cookies from JSON file."""
    path = get_cookie_path()
    with open(path, 'r') as f:
        return json.load(f)

def save_cookies(cookies: dict) -> None:
    """Save cookies to JSON file."""
    path = get_cookie_path()
    with open(path, 'w') as f:
        json.dump(cookies, f)
```

For details, see `xhs_cli/cookies.py` and the functions:
- `get_cookies()` — Load + validate TTL
- `save_cookies()` — Persist to disk
- `cache_note_context()` — Cache token by note ID
- `load_note_index()` — Load CLI shortcut cache

---

## No Database Work Required

If a new feature requires persistent storage:

1. **Ask**: Does it really need persistence across process restarts?
2. **Use JSON** if storing simple config/cache (see `cookies.py` pattern)
3. **Avoid**: Don't add a database dependency unless absolutely necessary

This keeps the project lightweight and easy to distribute as a CLI tool.

---

## Related Guidelines

For all other development standards, see:
- [`directory-structure.md`](./directory-structure.md) — File organization
- [`error-handling.md`](./error-handling.md) — Exception handling
- [`logging-guidelines.md`](./logging-guidelines.md) — Logging standards
- [`quality-guidelines.md`](./quality-guidelines.md) — Code quality (Lint, Type Check, Tests)

