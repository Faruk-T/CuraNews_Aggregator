"""PII pseudonymization and scrubbing — Issues #13/#15."""

from curanews.privacy.pii import (
    EMAIL_REDACTION,
    HANDLE_REDACTION,
    PHONE_REDACTION,
    scrub_news_article_pii,
    scrub_pii,
)

__all__ = [
    "EMAIL_REDACTION",
    "HANDLE_REDACTION",
    "PHONE_REDACTION",
    "scrub_news_article",
    "scrub_news_article_pii",
    "scrub_pii",
    "scrub_text",
]


def __getattr__(name: str):
    if name in {"scrub_news_article", "scrub_text"}:
        from curanews.privacy import scrub as scrub_mod

        return getattr(scrub_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
