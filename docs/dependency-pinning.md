# Dependency pinning

CuraNews uses **Poetry** for dependency pinning (Issue #2 / ADR-005).

## Why

- Every developer and CI environment resolves the **same package versions**
- Security/review is easier when upgrades are intentional (`poetry update`)
- The application package (`curanews`) is installable from `src/` layout

## Files

| File | Role |
|------|------|
| `pyproject.toml` | Direct dependencies + tool config (pytest, ruff) |
| `poetry.lock` | Locked transitive graph — **commit this file** |
| `.env.example` | Non-secret settings template |

## Setup

```powershell
# Python 3.11–3.13 required (3.12 recommended)
python -m pip install poetry
poetry env use python
poetry install
poetry run python -m curanews
poetry run pytest
```

Playwright browsers and spaCy models are **not** in the lockfile install step; they are downloaded when those features are wired (later issues):

```powershell
poetry run playwright install
poetry run python -m spacy download en_core_web_sm
```

## Upgrade policy

1. Change the constraint in `pyproject.toml`
2. Run `poetry lock` (or `poetry update <package>`)
3. Run tests
4. Commit both `pyproject.toml` and `poetry.lock`
