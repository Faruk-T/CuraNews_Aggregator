# Day 9 evidence (Issue #9)

| File | What it shows |
|------|----------------|
| `pytest-parallel.png` | Green `tests/unit/test_parallel_ingest.py` |
| `run-parallel-fetch.png` | JSON with `wall_seconds` < `sequential_estimate_seconds` |
| `browser-demo.png` | (optional) `--browser-demo` concurrent tabs |

Commands:

```powershell
poetry run pytest tests/unit/test_parallel_ingest.py -q
poetry run python scripts/run_parallel_fetch.py --adapters static,api --concurrency 2
poetry run playwright install chromium
poetry run python scripts/run_parallel_fetch.py --browser-demo
```
