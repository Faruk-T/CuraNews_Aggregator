# spaCy NLP (Issue #14 / G14)

Extract named entities and rule-based topics from article text, then store them in
`entities` / `article_entities` (IMPLEMENTATION_PLAN §7.2).

## Install model

```powershell
poetry run python -m spacy download en_core_web_sm
```

`.env` / settings default:

```env
SPACY_MODEL=en_core_web_sm
```

## Verify

```powershell
poetry run pytest tests/unit/test_spacy_nlp.py -q
poetry run python scripts/verify_spacy_nlp.py
poetry run python scripts/verify_spacy_nlp.py --require-model
# optional live DB:
docker compose up -d postgres
poetry run alembic upgrade head
poetry run python scripts/verify_spacy_nlp.py --persist
```

## Degrade strategy

| Situation | Behaviour |
|-----------|-----------|
| Model missing / load error | `SpacyPipe.available=False`; NER skipped; **TOPIC** keywords still run |
| Empty text | Empty entity list |
| `--require-model` CLI | Hard fail with install hint |

Ingestion continues when spaCy is down (`entities_linked` may still rise from TOPIC keywords).

## Modules

| Module | Role |
|--------|------|
| `nlp/spacy_pipe.py` | Load model, NER extract, degrade logging |
| `nlp/topics.py` | TR/EN keyword → `TOPIC:*` tags |
| `nlp/tagging.py` | Article text → DB links |
| `db/entity_repository.py` | `ensure_entity` + `article_entities` |

## Ingestion hook

`IngestionPipeline(run_nlp=True)` tags each newly inserted article. Disable with:

```powershell
poetry run python scripts/run_ingestion.py --adapter static --no-nlp
```

## Related

- [`ingestion-pipeline.md`](./ingestion-pipeline.md)
- [`postgresql-schema.md`](./postgresql-schema.md)
