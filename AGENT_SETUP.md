# Agent setup guide — My Verisure

Quick reference for the Cursor agent configuration in this repository.

## Setup status

### Installed skills

See `.agents/skills/` and `.agents/SKILLS_INSTALLED.md` for the full catalog. Core skills include:

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `writing-plans` | Create implementation plans | Before large, multi-step work |
| `executing-plans` | Execute a written plan step by step | When a plan file already exists |
| `to-prd` | Turn context into a structured PRD | Product decisions and scope |
| `to-issues` | Break work into GitHub issues | Backlog and tracking |
| `verification-before-completion` | Verify before claiming done | **Always** before commits and PRs |
| `systematic-debugging` | Structured debugging | Reproduce and fix bugs |
| `improve-codebase-architecture` | Architecture review | Technical debt and refactors |
| `generate-readme` | Generate or refresh README-style docs | After meaningful doc changes |
| `find-skills` | Discover skills in the ecosystem | Extend agent capabilities |
| `ha-integration-dev` | Home Assistant integration patterns | `custom_components` work |
| `code-review-excellence` | Structured code review | PR review and quality |
| `python-code-style` | Python style and tooling | New or refactored Python |
| `python-testing-patterns` | Pytest patterns and strategy | Tests and test design |

### Active rules (5)

| Rule | Scope | Purpose |
|------|-------|---------|
| `session-info` | Always apply | Session summary: skills, rules, RTK |
| `python-standards` | `**/*.py` | Modern Python conventions |
| `home-assistant-integration` | `custom_components/**/*.py` | Non-negotiable HA integration rules |
| `testing-standards` | `**/tests/**/*.py` | Pytest, AAA, coverage targets |
| `documentation-standards` | `**/*.md` | README, docstrings, ADRs |

### RTK

- **Installed** (example path): `/opt/homebrew/bin/rtk` — run `which rtk` on your machine
- **Typical version**: check with `rtk --version`
- **Effect**: can reduce token use by roughly 60–90% via shell command rewriting
- **Integration**: Cursor hooks when configured

---

## First session

At the start of a new chat you should see something like:

```
---
Session info

Skills available: [N] skills
Active rules: 5 rules
RTK: Active (or Not detected)

Say "list skills" or "show rules" for details.
---
```

---

## Useful commands

### Skills

```bash
# List installed skill folders
ls -la .agents/skills/

# Open one skill’s definition
cat .agents/skills/writing-plans/SKILL.md

# Catalog with usage notes
cat .agents/SKILLS_INSTALLED.md
```

### Rules

```bash
ls -la .cursor/rules/
cat .cursor/rules/python-standards.mdc

# Quick peek at all rule headers
for f in .cursor/rules/*.mdc; do echo "=== $f ==="; head -10 "$f"; echo; done
```

### RTK

```bash
rtk --version
rtk rewrite "pytest tests/ -v"
rtk stats   # if configured
```

---

## Usage examples

### Example 1: New feature

**You:** “I need Verisure camera support.”

**Agent (illustrative):** Uses `writing-plans`, saves e.g. `docs/superpowers/plans/YYYY-MM-DD-verisure-cameras.md`, then offers execution with `executing-plans`.

### Example 2: Debugging

**You:** “`arm_away` fails with 401.”

**Agent (illustrative):** Uses `systematic-debugging` — reproduce, inspect logs, fix (e.g. token refresh), verify with `verification-before-completion`, add a regression test.

### Example 3: Test hygiene

**You:** “Tests feel messy.”

**Agent (illustrative):** Applies `testing-standards.mdc` — AAA, names like `test_should_X_when_Y`, shared fixtures in `conftest.py`, coverage goals 80–90%; may propose a `writing-plans` refactor plan.

---

## Non-negotiable rules

The agent must not violate these for Home Assistant code under `custom_components/**/*.py`:

```python
# ✅ ALWAYS
from homeassistant.util import dt as dt_util
now = dt_util.now()

# ❌ NEVER
from datetime import datetime
now = datetime.now()
```

```python
# ✅ ALWAYS — aiohttp
import aiohttp
async with aiohttp.ClientSession() as session:
    response = await session.get(url)

# ❌ NEVER — requests in async integration code
import requests
response = requests.get(url)
```

```python
# ✅ ALWAYS — use entry.runtime_data for ConfigEntry-owned runtime state
entry.runtime_data = coordinator

# ❌ NEVER — do not introduce new hass.data patterns for this
hass.data[DOMAIN] = coordinator
```

### Verification

```text
# ✅ ALWAYS before commit
# 1. Run the real test command (e.g. pytest)
# 2. Read full output
# 3. Confirm zero failures
# 4. Then commit

# ❌ NEVER
# “Tests should pass”
# “Looks fine”
# commit without verification
```

---

## Further reading

- **Skills**: `.agents/SKILLS_INSTALLED.md` — per-skill usage
- **Recommendations**: `.agents/RECOMMENDED_SKILLS.md` — optional ecosystem skills
- **Agent layout**: `.agents/README.md` — how `.agents/` is organized
- **Project**: `README.md` — product and developer docs

---

## Troubleshooting

### Skills not visible

```bash
ls -la .agents/skills/
head -5 .agents/skills/writing-plans/SKILL.md   # check YAML frontmatter
```

### Rules not applying

```bash
ls -la .cursor/rules/*.mdc
head -5 .cursor/rules/python-standards.mdc      # description, globs, alwaysApply
```

### RTK issues

```bash
which rtk
rtk --version
# Reinstall if needed, e.g. brew reinstall rtk  OR  pip install --upgrade rtk-cli
```

---

## Practices

1. **Plan before large changes:** `writing-plans` → `executing-plans`; small edits can go direct.
2. **Verify always:** changes → `verification-before-completion` → commit — not commit on hope.
3. **Chain skills when useful:** e.g. discussion → `to-prd` → `to-issues` → `writing-plans` → `executing-plans`.
4. **Debug systematically:** bug → `systematic-debugging` → fix → verify → regression test.
5. **Record decisions:** architecture → ADR under `docs/adr/`; user-facing changes → refresh docs (`generate-readme` when appropriate).

---

## Skill status legend

| Status | Meaning |
|--------|---------|
| Installed | Present under `.agents/skills/` and ready to use |
| Recommended | Listed in `RECOMMENDED_SKILLS.md` |
| In use | Currently driving the session |
| Experimental | Use with care |

---

## Project metrics (reference)

### Testing

- **Total tests** (per README): 229  
- **CLI / core split**: see `README.md` / `TESTING.md`  
- **Coverage target**: 80–90% for new and critical paths  

### Code quality

- **Linter / formatter**: prefer **ruff** (can replace black + flake8 + isort)  
- **Types**: mypy  
- **Runner**: pytest  
- **CI/CD**: wire GitHub Actions as needed  

### Documentation

- **README**: keep in sync with behavior  
- **`.agents/`**: skill and agent docs  
- **`.cursor/rules`**: Cursor rule definitions  
- **API / entities**: docstrings and guides (e.g. entity docs)  

---

## Next steps

### Done in repo

1. Skills under `.agents/skills/`  
2. Rules under `.cursor/rules/`  
3. RTK optional but recommended  
4. Supporting docs under `.agents/`  

### Short term

1. Install any high-priority skills from `RECOMMENDED_SKILLS.md` you still want globally or per-repo.  
2. Run one full loop: plan → execute → verify.  
3. Optionally migrate lint/format to ruff if not already.  

### Medium term — historical setup recommendations

1. Add code-review workflow skills if useful for your team.  
2. Harden CI (completed; see `.github/workflows/validate.yml`).
3. Raise coverage toward 85%+ on core modules when risk-based tests justify it.

---

## Getting help

### In chat

Examples:

- “What skills are installed?”  
- “Show the Python rules.”  
- “How do I use writing-plans?”  
- “List documentation-related skills.”  

### On disk

```bash
cat .agents/SKILLS_INSTALLED.md
cat .agents/RECOMMENDED_SKILLS.md
cat AGENT_SETUP.md
```

---

**Last updated:** 2026-08-13
**Rules:** 5 active under `.cursor/rules/`  
**RTK:** use `which rtk` / `rtk --version` on your machine  
**Status:** ready for day-to-day use  
