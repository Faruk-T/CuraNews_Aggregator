"""Source adapter contract — unify ingestion paths (Issue #8 / G8)."""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from curanews.domain.models import RawArticleDraft


@runtime_checkable
class SourceAdapter(Protocol):
    """Fetch normalized drafts from a single news source."""

    source_id: str
    kind: Literal["static", "dynamic", "api"]

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        """Return up to ``limit`` drafts for validation and persistence."""


def adapter_label(adapter: SourceAdapter) -> str:
    return f"{adapter.source_id} ({adapter.kind})"
