"""Server-rendered pages: home shell, article permalinks and category listings."""

from __future__ import annotations

import logging
from functools import lru_cache
from html import escape
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.api.feed_service import ANONYMOUS_CACHE_KEY, build_feed_response
from curanews.api.routers.feed import get_feed_cache
from curanews.api.schemas import ArticleItem
from curanews.api.services import article_to_item, list_articles
from curanews.api.urls import base_path, public_base_url, slugify
from curanews.cache.feed_cache import FeedCache
from curanews.config import get_settings
from curanews.db.models import Article
from curanews.nlp.categorizer import CANONICAL_CATEGORIES, category_aliases
from curanews.web.render import (
    ASSET_VERSION,
    CATEGORY_DESCRIPTIONS,
    SITE_DESCRIPTION,
    SITE_NAME,
    SITE_TAGLINE,
    WEB_DIR,
    attr,
    breadcrumb_ld,
    card_html,
    category_href,
    clip,
    head_tags,
    human_date,
    iso,
    json_ld,
    organization_ld,
    page_shell,
)

logger = logging.getLogger(__name__)

router = APIRouter(include_in_schema=False)

HOME_SSR_ITEMS = 24
CATEGORY_PAGE_SIZE = 30
RELATED_ITEMS = 6


def _html(content: str, *, status_code: int = 200, max_age: int = 120) -> HTMLResponse:
    return HTMLResponse(
        content,
        status_code=status_code,
        headers={"Cache-Control": f"public, max-age={max_age}"},
    )


@lru_cache(maxsize=1)
def _index_template() -> str:
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


def _article_url(base: str, item: ArticleItem) -> str:
    return f"{base}/{item.page_path}"


# --------------------------------------------------------------------------- home


@router.get("/ui/", response_class=HTMLResponse)
@router.get("/ui/index.html", response_class=HTMLResponse)
def home_page(
    request: Request,
    session: Session = Depends(get_db),
    cache: FeedCache = Depends(get_feed_cache),
) -> HTMLResponse:
    base = public_base_url(request)
    settings = get_settings()
    try:
        items = build_feed_response(
            session, user_id=ANONYMOUS_CACHE_KEY, limit=HOME_SSR_ITEMS, cache=cache
        ).items
    except Exception:  # noqa: BLE001 — the shell must render even if ranking fails
        logger.exception("home SSR feed failed")
        items = []

    canonical = f"{base}/ui/"
    title = f"{SITE_NAME} — Güncel Haberler, Son Dakika ve Gündem"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            organization_ld(base),
            {
                "@type": "WebSite",
                "@id": f"{base}/#website",
                "url": canonical,
                "name": SITE_NAME,
                "description": SITE_DESCRIPTION,
                "inLanguage": "tr-TR",
                "publisher": {"@id": f"{base}/#organization"},
            },
            {
                "@type": "ItemList",
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "url": _article_url(base, item)}
                    for i, item in enumerate(items[:10], start=1)
                ],
            },
        ],
    }
    config_meta = [f'<meta name="curanews-base" content="{attr(base_path(request))}" />']
    if settings.ga_measurement_id:
        ga_id = attr(settings.ga_measurement_id)
        config_meta.append(f'<meta name="curanews-ga" content="{ga_id}" />')
    head = head_tags(
        title=title,
        description=SITE_DESCRIPTION,
        canonical=canonical,
        base=base,
        extra=[*config_meta, json_ld(ld)],
    )

    featured = ""
    cards = ""
    if items:
        featured = card_html(items[0], href=f"../{items[0].page_path}", featured=True)
        cards = "".join(card_html(item, href=f"../{item.page_path}") for item in items[1:])

    html = (
        _index_template()
        .replace("<!--SSR:HEAD-->", head)
        .replace("<!--SSR:FEATURED-->", featured)
        .replace("<!--SSR:FEED-->", cards)
        .replace("__ASSET_VERSION__", ASSET_VERSION)
    )
    if featured:
        html = html.replace(
            'id="featuredSlot" class="featured" hidden', 'id="featuredSlot" class="featured"'
        )
    return _html(html, max_age=60)


# ------------------------------------------------------------------------ article


@router.get("/haber/{article_id}")
def article_redirect(article_id: UUID, request: Request, session: Session = Depends(get_db)):
    article = session.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")
    return RedirectResponse(f"{article_id}/{slugify(article.title)}", status_code=301)


@router.get("/haber/{article_id}/{slug}", response_class=HTMLResponse)
def article_page(
    article_id: UUID,
    slug: str,
    request: Request,
    session: Session = Depends(get_db),
) -> HTMLResponse:
    article = session.get(Article, article_id)
    if article is None:
        return _not_found(request)
    canonical_slug = slugify(article.title)
    if slug != canonical_slug:
        return RedirectResponse(canonical_slug, status_code=301)  # type: ignore[return-value]

    base = public_base_url(request)
    item = article_to_item(session, article)
    canonical = _article_url(base, item)
    category_slug = item.category or "gundem"
    category_name = item.category_name or "Gündem"
    description = clip(item.summary or item.body or item.title, 158)

    related = _related(session, article, category_slug)

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "NewsArticle",
                "headline": clip(item.title, 110),
                "description": description,
                "image": [item.image_url] if item.image_url else [],
                "datePublished": iso(item.published_at),
                "dateModified": iso(item.published_at),
                "articleSection": category_name,
                "inLanguage": "tr-TR",
                "mainEntityOfPage": canonical,
                "isAccessibleForFree": True,
                "author": (
                    {"@type": "Person", "name": item.author_display}
                    if item.is_editorial and item.author_display
                    else {"@type": "Organization", "name": item.source_name}
                ),
                "publisher": organization_ld(base),
                **({} if item.is_editorial else {"isBasedOn": item.url}),
            },
            breadcrumb_ld(
                [
                    ("Ana Sayfa", f"{base}/ui/"),
                    (category_name, category_href(base, category_slug)),
                    (clip(item.title, 80), canonical),
                ]
            ),
        ],
    }
    extra = [
        f'<meta property="article:published_time" content="{iso(item.published_at)}" />',
        f'<meta property="article:section" content="{attr(category_name)}" />',
        json_ld(ld),
    ]
    head = head_tags(
        title=f"{clip(item.title, 70)} | {SITE_NAME}",
        description=description,
        canonical=canonical,
        base=base,
        og_type="article",
        image=item.image_url,
        extra=extra,
    )
    body = _article_body(base, item, related)
    return _html(page_shell(head=head, base=base, body=body, active_category=category_slug))


def _related(session: Session, article: Article, category_slug: str) -> list[ArticleItem]:
    rows = session.scalars(
        select(Article)
        .where(Article.id != article.id)
        .where(Article.category.in_(category_aliases(category_slug)))
        .order_by(Article.published_at.desc().nulls_last())
        .limit(RELATED_ITEMS)
    ).all()
    return [article_to_item(session, row) for row in rows]


def _paragraphs(text: str) -> list[str]:
    blocks = [" ".join(p.split()) for p in text.replace("\r", "").split("\n\n")]
    return [p for p in blocks if p]


def _article_body(base: str, item: ArticleItem, related: list[ArticleItem]) -> str:
    summary = (item.summary or "").strip()
    body = (item.body or "").strip()
    paragraphs = _paragraphs(body) if body and body != summary else []
    if paragraphs and " ".join(paragraphs[0].split()) == " ".join(summary.split()):
        paragraphs = paragraphs[1:]

    category_slug = item.category or "gundem"
    category_name = item.category_name or "Gündem"
    when = human_date(item.published_at)

    parts = [
        '<article class="page-article">',
        '<nav class="breadcrumb" aria-label="Sayfa konumu">'
        f'<a href="{attr(base)}/ui/">Ana Sayfa</a><span aria-hidden="true">›</span>'
        f'<a href="{attr(category_href(base, category_slug))}">{attr(category_name)}</a></nav>',
        '<p class="page-kicker">'
        f'<a class="badge-cat" href="{attr(category_href(base, category_slug))}">'
        f"{attr(category_name)}</a>"
        f'<time datetime="{iso(item.published_at)}">{when}</time>'
        f"<span>{item.read_time_minutes} dk okuma</span></p>",
        f'<h1 class="page-title">{attr(item.title)}</h1>',
    ]
    if summary:
        parts.append(f'<p class="page-lead">{attr(summary)}</p>')
    byline = (
        f"{attr(item.author_display)} · {attr(item.author_title or 'CuraNews Editör Masası')}"
        if item.is_editorial and item.author_display
        else f"Kaynak: <strong>{attr(item.source_name)}</strong>"
    )
    parts.append(f'<p class="page-byline">{byline}</p>')
    if item.image_url:
        parts.append(
            '<figure class="page-hero">'
            f'<img src="{attr(item.image_url)}" alt="{attr(item.title)}" fetchpriority="high" />'
            "</figure>"
        )
    if item.video_url:
        parts.append(
            '<div class="modal-video-wrap"><iframe class="modal-video-iframe" '
            f'src="{attr(item.video_url)}" title="{attr(item.title)}" loading="lazy" '
            'allow="encrypted-media; picture-in-picture" allowfullscreen></iframe></div>'
        )
    if paragraphs:
        parts.append(
            '<div class="page-body">'
            + "".join(f"<p>{escape(p)}</p>" for p in paragraphs)
            + "</div>"
        )
    if not item.is_editorial:
        parts.append(
            '<aside class="modal-attribution">'
            '<p class="attribution-text">Bu haber <strong>'
            f"{attr(item.source_name)}</strong> tarafından yayımlanmış ve resmi RSS akışı "
            "üzerinden özetlenmiştir. Tüm hakları yayıncısına aittir.</p>"
            f'<a class="btn-external-source" href="{attr(item.url)}" target="_blank" '
            f'rel="noopener">Haberin tamamını {attr(item.source_name)} sitesinde okuyun ↗</a>'
            "</aside>"
        )
    parts.append(
        '<p class="page-cta"><a class="btn primary" '
        f'href="{attr(base)}/ui/?haber={item.id}">'
        "Yorumlar ve kişisel akış için CuraNews'te aç</a></p>"
    )
    parts.append("</article>")

    if related:
        cards = "".join(card_html(r, href=_article_url(base, r)) for r in related)
        parts.append(
            '<section class="page-related" aria-labelledby="ilgili">'
            f'<h2 id="ilgili">{attr(category_name)} kategorisinden diğer haberler</h2>'
            f'<ol class="feed-grid">{cards}</ol></section>'
        )
    return "\n".join(parts)


# ----------------------------------------------------------------------- category


@router.get("/kategori/{slug}", response_class=HTMLResponse)
def category_page(
    slug: str,
    request: Request,
    sayfa: int = Query(default=1, ge=1, le=200),
    session: Session = Depends(get_db),
) -> HTMLResponse:
    if slug not in CANONICAL_CATEGORIES:
        return _not_found(request)
    base = public_base_url(request)
    name = CANONICAL_CATEGORIES[slug]
    rows, total = list_articles(
        session,
        offset=(sayfa - 1) * CATEGORY_PAGE_SIZE,
        limit=CATEGORY_PAGE_SIZE,
        category=slug,
    )
    items = [article_to_item(session, row) for row in rows]
    pages = max(1, -(-total // CATEGORY_PAGE_SIZE))
    if sayfa > pages and total:
        return _not_found(request)

    self_url = category_href(base, slug) + ("" if sayfa == 1 else f"?sayfa={sayfa}")
    title = f"{name} Haberleri" + ("" if sayfa == 1 else f" — Sayfa {sayfa}")
    description = CATEGORY_DESCRIPTIONS.get(slug, SITE_TAGLINE)
    extra = [
        json_ld(
            {
                "@context": "https://schema.org",
                "@graph": [
                    {
                        "@type": "CollectionPage",
                        "name": f"{name} Haberleri",
                        "url": self_url,
                        "description": description,
                        "isPartOf": {"@id": f"{base}/#website"},
                    },
                    breadcrumb_ld([("Ana Sayfa", f"{base}/ui/"), (f"{name} Haberleri", self_url)]),
                ],
            }
        )
    ]
    category_url = category_href(base, slug)
    prev_url = category_url + ("" if sayfa == 2 else f"?sayfa={sayfa - 1}")
    next_url = f"{category_url}?sayfa={sayfa + 1}"
    if sayfa > 1:
        extra.append(f'<link rel="prev" href="{attr(prev_url)}" />')
    if sayfa < pages:
        extra.append(f'<link rel="next" href="{attr(next_url)}" />')

    head = head_tags(
        title=f"{title} | {SITE_NAME}",
        description=description,
        canonical=self_url,
        base=base,
        extra=extra,
    )
    cards = "".join(card_html(item, href=_article_url(base, item)) for item in items)
    pager = []
    if sayfa > 1:
        pager.append(
            f'<a class="btn secondary" rel="prev" href="{attr(prev_url)}">← Daha yeni haberler</a>'
        )
    if sayfa < pages:
        pager.append(
            f'<a class="btn secondary" rel="next" href="{attr(next_url)}">Daha eski haberler →</a>'
        )
    listing = (
        f'<ol class="feed-grid">{cards}</ol>'
        if cards
        else '<p class="empty">Bu kategoride henüz haber yok.</p>'
    )
    pager_html = (
        f'<nav class="page-pager" aria-label="Sayfalar">{"".join(pager)}</nav>' if pager else ""
    )
    body = (
        '<section class="feed-section">'
        '<div class="feed-meta"><div>'
        f'<p class="section-kicker">{SITE_NAME} · Kategori</p>'
        f"<h1>{attr(title)}</h1>"
        f'<p class="feed-count">{attr(description)}</p>'
        "</div></div>"
        f"{listing}{pager_html}</section>"
    )
    return _html(page_shell(head=head, base=base, body=body, active_category=slug))


def _not_found(request: Request) -> HTMLResponse:
    base = public_base_url(request)
    head = head_tags(
        title=f"Sayfa bulunamadı | {SITE_NAME}",
        description=SITE_DESCRIPTION,
        canonical=f"{base}/ui/",
        base=base,
        robots="noindex, follow",
    )
    body = (
        '<section class="feed-section page-article">'
        '<h1 class="page-title">Aradığınız haber bulunamadı</h1>'
        '<p class="page-lead">Haber kaldırılmış ya da bağlantı hatalı olabilir.</p>'
        f'<p><a class="btn primary" href="{attr(base)}/ui/">Güncel haberlere dön</a></p>'
        "</section>"
    )
    return _html(page_shell(head=head, base=base, body=body), status_code=404, max_age=30)
