# Day 8 evidence (Issue #8 / G8)

| File | What it shows |
|------|----------------|
| `pytest-adapters.png` | Green run of `tests/test_source_adapters.py` |
| `fetch-sources-list.png` | Output of `fetch_sources.py --list` |
| `fetch-sources-api.png` | JSON summary from `--adapter api --promote` |
| `fetch-sources-static.png` | (optional) `--adapter static --promote` |

Commands:

```powershell
poetry run pytest tests/test_source_adapters.py -q
poetry run python scripts/fetch_sources.py --list
poetry run python scripts/fetch_sources.py --adapter api --promote --limit 5
```
