# Day 14 evidence (Issue #14 / G14)

## Code block screenshots (IDE)

| File | Screenshot | Highlight |
|------|------------|-----------|
| `src/curanews/nlp/spacy_pipe.py` | `code-spacy-extract.png` | `extract()` + degrade path |
| `src/curanews/nlp/topics.py` | `code-topic-keywords.png` | TR/EN keyword map |
| `src/curanews/db/entity_repository.py` | `code-entity-repository.png` | `attach_extracted()` |
| `src/curanews/ingestion/pipeline.py` | `code-ingest-nlp-hook.png` | `run_nlp` + `tag_article` |

## Terminal (Ek-24 önerisi)

```powershell
poetry run python -m spacy download en_core_web_sm
poetry run pytest tests/unit/test_spacy_nlp.py -q
poetry run python scripts/verify_spacy_nlp.py --require-model
```

Show at least one `ORG` / `GPE` / `TOPIC` in JSON. Optional: `--persist` against Postgres.

## Staj defteri

Note EN model + rule-based TR topics, degrade when model missing, and `article_entities` persistence.
