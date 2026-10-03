"""Build personalized feeds with Redis cache (Issue #17 / G17)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.schemas import ArticleItem, FeedResponse
from curanews.api.services import article_to_item
from curanews.cache.feed_cache import CacheOutcome, FeedCache
from curanews.config import get_settings
from curanews.db.models import Article
from curanews.db.user_repository import UserRepository
from curanews.nlp.curation import CurationEngine


def feed_query(*, limit: int) -> dict[str, Any]:
    return {"limit": limit}


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def still_on_main_feed(
    read_at: datetime | None,
    *,
    now: datetime,
    grace_seconds: int,
) -> bool:
    """Unread items stay on Akış; read items stay until the grace window elapses."""
    if read_at is None:
        return True
    return _aware(now) - _aware(read_at) <= timedelta(seconds=grace_seconds)


def build_feed_response(
    session: Session,
    *,
    user_id: str,
    limit: int,
    cache: FeedCache | None = None,
    now: datetime | None = None,
) -> FeedResponse:
    """Return scored feed; use Redis HIT when possible, else compute + SET."""
    users = UserRepository(session)
    user = users.get_by_external_key(user_id)
    if user is None:
        if user_id in ("demo-editor", "demo-okur", "demo-user-a", "demo-user-b"):
            from curanews.api.routers.auth import ensure_demo_accounts

            ensure_demo_accounts(session)
            user = users.get_by_external_key(user_id)
        if user is None:
            raise LookupError(f"user {user_id!r} not found — seed demo users")


    query = feed_query(limit=limit)
    feed_cache = cache or FeedCache()
    cached = feed_cache.get(user_id, query)

    if cached.outcome == CacheOutcome.HIT and isinstance(cached.payload, dict):
        payload = dict(cached.payload)
        payload["cache"] = "hit"
        return FeedResponse.model_validate(payload)

    clock = now or datetime.now(UTC)
    grace_seconds = get_settings().read_inbox_grace_seconds
    read_times = users.read_times(user.id)
    stale_ids = {
        article_id
        for article_id, read_at in read_times.items()
        if not still_on_main_feed(read_at, now=clock, grace_seconds=grace_seconds)
    }

    candidates = list(session.scalars(select(Article)).all())
    if not candidates:
        import hashlib
        import uuid
        from curanews.db.models import Source

        ed_source = session.scalars(select(Source).where(Source.name == "CuraNews Editör Masası")).first()
        if not ed_source:
            ed_source = Source(
                name="CuraNews Editör Masası",
                base_url="https://truncgil.com/",
                kind="editorial",
                enabled=True,
                robots_respected=True,
            )
            session.add(ed_source)
            session.flush()

        initial_seeds = [
            (
                "CuraNews Canlı Yayında: Truncgil Teknoloji Altyapısıyla Akıllı Haber Akışı Başladı",
                "gundem",
                "Truncgil Teknoloji bünyesinde geliştirilen yeni nesil akıllı haber kürasyon ve editör masası platformu CuraNews resmi olarak canlı yayına başladı. Gündem, ekonomi, teknoloji ve spor başlıkları yapay zeka destekli akıllı bülten ile okurlara sunuluyor.",
            ),
            (
                "Yapay Zeka ve Büyük Dil Modellerinde Yeni Atılımlar",
                "teknoloji",
                "Açık kaynaklı yapay zeka modelleri ve otonom yazılım asistanları geliştirici ekosisteminde yeni bir dönem başlatıyor. Yerli ve küresel teknoloji şirketleri inovasyon yatırımlarını artırıyor.",
            ),
            (
                "Küresel Piyasalarda Faiz İndirimi Beklentisi ve Borsa Rallisi",
                "ekonomi",
                "Merkez bankalarının para politikası adımları öncesinde küresel hisse senedi piyasalarında ve yatırım fonlarında hareketlilik hız kazandı. Analistler dengeli portföy yönetimini öneriyor.",
            ),
            (
                "Süper Lig'de Heyecan Dorukta: Haftanın Kritik Karşılaşmaları",
                "spor",
                "Lig maratonunda zirve yarışında kritik haftaya girildi. Takımların form durumları, sakatlık raporları ve taktiksel saha analizleri taraftarların odağında.",
            ),
        ]
        for title, cat, body in initial_seeds:
            u_hash = hashlib.sha256(title.encode("utf-8")).hexdigest()
            art = Article(
                id=uuid.uuid4(),
                source_id=ed_source.id,
                url=f"https://truncgil.com/curanews/article/{u_hash[:12]}",
                url_hash=u_hash,
                title=title,
                body=body,
                summary=body[:140],
                content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
                category=cat,
                language="tr",
                published_at=clock,
            )
            session.add(art)
        session.commit()
        candidates = list(session.scalars(select(Article)).all())

    inbox_candidates = [article for article in candidates if article.id not in stale_ids]

    ranked = CurationEngine(session).rank(
        user.id, inbox_candidates, top_k=limit, hide_read=False, now=clock
    )
    items: list[ArticleItem] = [
        article_to_item(
            session,
            scored.article,
            score=round(scored.score, 4),
            read=scored.article.id in read_times,
            read_at=read_times.get(scored.article.id),
        )
        for scored in ranked
    ]
    read_items = _read_archive(
        session,
        candidates=candidates,
        read_times=read_times,
        limit=limit,
    )
    cache_status = "bypass" if cached.outcome == CacheOutcome.BYPASS else "miss"
    response = FeedResponse(
        user_id=user_id,
        generated_at=clock,
        cache=cache_status,  # type: ignore[arg-type]
        items=items,
        read_items=read_items,
        inbox_grace_seconds=grace_seconds,
    )
    # Store without forcing cache flag so HIT responses can overwrite to "hit"
    to_store = response.model_dump(mode="json")
    to_store["cache"] = "miss"
    feed_cache.set(user_id, query, to_store)
    return response


def _read_archive(
    session: Session,
    *,
    candidates: list[Article],
    read_times: dict[UUID, datetime],
    limit: int,
) -> list[ArticleItem]:
    """Okunanlar tab: all marked-read articles, newest first (grace does not apply)."""
    by_id = {article.id: article for article in candidates if article.id in read_times}
    ordered = sorted(
        by_id.values(),
        key=lambda article: _aware(read_times[article.id]),
        reverse=True,
    )
    return [
        article_to_item(
            session,
            article,
            read=True,
            read_at=read_times[article.id],
        )
        for article in ordered[:limit]
    ]
