# News data model (Issue #3)

Day 3 defines the **canonical news schema** used by Scrapy items and Pydantic domain models.

## Required fields (Issue #3)

| Field | Type | Notes |
|-------|------|-------|
| `article_id` | UUID | Unique ID (auto-generated when promoting drafts) |
| `title` | string | Non-empty, trimmed |
| `url` | URL | Valid HTTP(S) URL |
| `content` | string | Main body text |
| `published_date` | datetime | Publication timestamp |
| `source` | string | Publisher / site key |
| `category` | string | Normalized to lowercase-kebab |

## Optional fields

`summary`, `author`, `language`, `scraped_at`, `metadata`

## Modules

| Module | Role |
|--------|------|
| `curanews.domain.models.NewsArticle` | Strict Pydantic model (API/DB boundary) |
| `curanews.scrapers.items.NewsItem` | Scrapy `Item` with the same required fields |
| `curanews.scrapers.validators` | Fail-fast checks against silent corruption |
| `curanews.scrapers.pipelines.NewsItemValidationPipeline` | Drops/raises on incomplete items |

## Anti-corruption rule

Incomplete payloads **must not** be persisted. Validation raises `IncompleteNewsItemError` when any required field is missing or blank.

```text
Spider yield NewsItem
        │
        ▼
NewsItemValidationPipeline ──fail──► log + drop/raise
        │ ok
        ▼
news_article_from_item() → NewsArticle → (later) DB
```

## Evidence

Screenshots / diagrams for the internship notebook live under `docs/evidence/day-3/`.
