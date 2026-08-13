# Code style

- Prefer **type hints** on new code (`list[str]`, `str | None`).  
- Use **`aiohttp`** for HTTP inside integration paths — never `requests` in async contexts.  
- Timestamps in HA-facing attributes should be **ISO strings**, not raw `datetime` objects.  
- Follow Google-style **docstrings** for public helpers.  
- Align with project guidance in [`.cursor/rules/python-standards.mdc`](../../.cursor/rules/python-standards.mdc).  

Run `make lint-critical` and `make type-check-migrated` before PRs; the exact
Home Assistant test stack is pinned in `requirements-dev.txt`.
