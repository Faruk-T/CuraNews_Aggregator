"""Algorithmic feed curation — IMPLEMENTATION_PLAN §7.5 (Issue #15 / G15)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from curanews.db.models import Article
from curanews.db.user_repository import UserRepository

# Default weights from IMPLEMENTATION_PLAN §7.5
W_FRESHNESS = 0.30
W_INTEREST = 0.45
W_DIVERSITY = 0.15
W_PENALTY = 0.10
FRESHNESS_LAMBDA = 0.02
DIVERSITY_LOOKBACK = 5


@dataclass(frozen=True, slots=True)
class ScoredArticle:
    article: Article
    score: float
    freshness: float
    interest: float
    diversity: float
    penalty: float


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def freshness_score(
    published_at: datetime | None,
    *,
    now: datetime | None = None,
    lambda_: float = FRESHNESS_LAMBDA,
) -> float:
    """Exponential decay by age in hours: e^{-λ Δt}."""
    if published_at is None:
        return 0.3
    current = now or datetime.now(timezone.utc)
    ts = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    delta_hours = max(0.0, (current - ts).total_seconds() / 3600.0)
    return math.exp(-lambda_ * delta_hours)


def penalty_score(article: Article, entity_count: int) -> float:
    """Higher penalty for thin / untagged content (0..1)."""
    score = 0.0
    if not (article.title or "").strip():
        score += 0.5
    summary = (article.summary or "").strip()
    body = (article.body or "").strip()
    if len(summary) < 20 and len(body) < 40:
        score += 0.3
    if entity_count == 0:
        score += 0.4
    return min(1.0, score)


def diversity_score(source_id: UUID, recent_source_ids: Sequence[UUID]) -> float:
    """1.0 if source not in recent window; decays with repeats."""
    if not recent_source_ids:
        return 1.0
    repeats = sum(1 for sid in recent_source_ids if sid == source_id)
    if repeats == 0:
        return 1.0
    return max(0.0, 1.0 - 0.35 * repeats)


@dataclass
class CurationEngine:
    """Score and rank candidate articles for a user."""

    session: Session
    w_t: float = W_FRESHNESS
    w_i: float = W_INTEREST
    w_d: float = W_DIVERSITY
    w_p: float = W_PENALTY
    _users: UserRepository | None = None

    def __post_init__(self) -> None:
        self._users = UserRepository(self.session)

    def score_article(
        self,
        article: Article,
        *,
        user_profile: set[str],
        recent_source_ids: Sequence[UUID] = (),
        now: datetime | None = None,
    ) -> ScoredArticle:
        article_ents = self._users.article_entity_set(article.id)  # type: ignore[union-attr]
        fresh = freshness_score(article.published_at, now=now)
        interest = jaccard(user_profile, article_ents)
        diversity = diversity_score(article.source_id, recent_source_ids)
        penalty = penalty_score(article, len(article_ents))
        total = (
            self.w_t * fresh
            + self.w_i * interest
            + self.w_d * diversity
            - self.w_p * penalty
        )
        return ScoredArticle(
            article=article,
            score=total,
            freshness=fresh,
            interest=interest,
            diversity=diversity,
            penalty=penalty,
        )

    def rank(
        self,
        user_id: UUID,
        candidates: Sequence[Article],
        *,
        now: datetime | None = None,
        top_k: int | None = None,
    ) -> list[ScoredArticle]:
        assert self._users is not None
        profile = self._users.entity_profile(user_id)
        ranked: list[ScoredArticle] = []
        recent: list[UUID] = []
        # Greedy: pick highest score given diversity vs already picked
        remaining = list(candidates)
        while remaining:
            best: ScoredArticle | None = None
            best_idx = -1
            for idx, article in enumerate(remaining):
                scored = self.score_article(
                    article,
                    user_profile=profile,
                    recent_source_ids=recent[-DIVERSITY_LOOKBACK:],
                    now=now,
                )
                if best is None or scored.score > best.score:
                    best = scored
                    best_idx = idx
            assert best is not None
            ranked.append(best)
            recent.append(best.article.source_id)
            remaining.pop(best_idx)
            if top_k is not None and len(ranked) >= top_k:
                break
        return ranked
