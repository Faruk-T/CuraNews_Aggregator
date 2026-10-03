"""HTML fragments shared by the article, category and home pages."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from curanews.api.schemas import ArticleItem
from curanews.config import get_settings
from curanews.nlp.categorizer import CANONICAL_CATEGORIES

ASSET_VERSION = "20261003"
FONTS_HREF = (
    "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700"
    "&amp;family=Outfit:wght@400;500;600;700&amp;family=Merriweather:wght@400;700"
    "&amp;display=swap"
)
SITE_NAME = "CuraNews"
SITE_TAGLINE = "Türkiye ve dünyadan güvenilir kaynaklardan derlenen güncel haberler"
SITE_DESCRIPTION = (
    "CuraNews; AA, TRT Haber, BBC Türkçe, NTV ve daha birçok resmi kaynaktan derlenen "
    "gündem, ekonomi, teknoloji, spor, sağlık ve dünya haberlerini tek akışta sunar."
)
CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "gundem": "Türkiye gündeminden son dakika gelişmeleri ve öne çıkan haberler.",
    "ekonomi": "Piyasalar, faiz, döviz, enflasyon ve iş dünyasından ekonomi haberleri.",
    "teknoloji": "Yapay zeka, yazılım, bilim ve dijital dünyadan teknoloji haberleri.",
    "spor": "Süper Lig, transfer, basketbol ve milli takımlardan spor haberleri.",
    "saglik": "Tıp, tedavi, halk sağlığı ve yaşamdan sağlık haberleri.",
    "dunya": "Uluslararası gelişmeler, diplomasi ve dünyadan son haberler.",
    "politika": "Meclis, seçimler ve siyasetten politika haberleri.",
}
WEB_DIR = Path(__file__).resolve().parents[3] / "web"


def attr(value: Any) -> str:
    return escape("" if value is None else str(value), quote=True)


def clip(text: str | None, limit: int) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def iso(value: datetime | None) -> str:
    if value is None:
        return ""
    stamp = value if value.tzinfo else value.replace(tzinfo=UTC)
    return stamp.astimezone(UTC).isoformat().replace("+00:00", "Z")


_TR_MONTHS = (
    "Ocak",
    "Şubat",
    "Mart",
    "Nisan",
    "Mayıs",
    "Haziran",
    "Temmuz",
    "Ağustos",
    "Eylül",
    "Ekim",
    "Kasım",
    "Aralık",
)


def human_date(value: datetime | None) -> str:
    if value is None:
        return ""
    stamp = (value if value.tzinfo else value.replace(tzinfo=UTC)).astimezone(UTC)
    local = stamp.timestamp() + 3 * 3600
    dt = datetime.fromtimestamp(local, tz=UTC)
    return f"{dt.day} {_TR_MONTHS[dt.month - 1]} {dt.year} {dt:%H:%M}"


def json_ld(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return '<script type="application/ld+json">' + payload.replace("</", "<\\/") + "</script>"


def head_tags(
    *,
    title: str,
    description: str,
    canonical: str,
    base: str,
    og_type: str = "website",
    image: str | None = None,
    extra: Iterable[str] = (),
    robots: str = "index, follow, max-image-preview:large",
) -> str:
    settings = get_settings()
    image_url = image or f"{base}/ui/og-default.png"
    tags = [
        f"<title>{attr(title)}</title>",
        f'<meta name="description" content="{attr(description)}" />',
        f'<meta name="robots" content="{attr(robots)}" />',
        f'<link rel="canonical" href="{attr(canonical)}" />',
        f'<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" '
        f'href="{attr(base)}/rss.xml" />',
        f'<link rel="icon" type="image/svg+xml" href="{attr(base)}/ui/favicon.svg" />',
        f'<meta property="og:site_name" content="{SITE_NAME}" />',
        '<meta property="og:locale" content="tr_TR" />',
        f'<meta property="og:type" content="{attr(og_type)}" />',
        f'<meta property="og:title" content="{attr(title)}" />',
        f'<meta property="og:description" content="{attr(description)}" />',
        f'<meta property="og:url" content="{attr(canonical)}" />',
        f'<meta property="og:image" content="{attr(image_url)}" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{attr(title)}" />',
        f'<meta name="twitter:description" content="{attr(description)}" />',
        f'<meta name="twitter:image" content="{attr(image_url)}" />',
    ]
    if settings.google_site_verification:
        tags.append(
            '<meta name="google-site-verification" '
            f'content="{attr(settings.google_site_verification)}" />'
        )
    tags.extend(extra)
    return "\n    ".join(tags)


def organization_ld(base: str) -> dict[str, Any]:
    return {
        "@type": "NewsMediaOrganization",
        "@id": f"{base}/#organization",
        "name": SITE_NAME,
        "url": f"{base}/ui/",
        "logo": {"@type": "ImageObject", "url": f"{base}/ui/logo-512.png"},
    }


def category_href(base: str, slug: str) -> str:
    return f"{base}/kategori/{slug}"


def card_html(item: ArticleItem, *, href: str, featured: bool = False) -> str:
    """Static card markup mirroring the classes app.js renders."""
    title = attr(item.title)
    summary = attr(clip(item.summary or item.body, 220))
    category = attr(item.category_name or "Gündem")
    source = attr(item.source_name)
    when = human_date(item.published_at)
    stamp = iso(item.published_at)
    image = attr(item.image_url or "")
    if featured:
        return (
            f'<div class="featured-media"><img src="{image}" alt="" class="featured-img" '
            f'fetchpriority="high" /></div>'
            '<div class="featured-content">'
            '<div class="featured-top-line">'
            f'<span class="badge-cat">{source}</span>'
            f'<span class="badge-cat">{category}</span>'
            f'<time class="time-read" datetime="{stamp}">{when}</time>'
            "</div>"
            f'<h2 class="featured-title"><a href="{attr(href)}">{title}</a></h2>'
            f'<p class="featured-summary">{summary}</p>'
            "</div>"
        )
    return (
        '<li class="feed-item">'
        f'<div class="card-media"><img src="{image}" alt="" class="card-img" '
        'loading="lazy" decoding="async" /></div>'
        '<div class="card-body">'
        '<div class="card-meta-top">'
        f'<span class="badge-cat">{source}</span>'
        f'<span class="badge-cat">{category}</span>'
        "</div>"
        f'<h3 class="card-title"><a href="{attr(href)}">{title}</a></h3>'
        f'<p class="card-summary">{summary}</p>'
        f'<div class="card-footer"><time class="time-read" datetime="{stamp}">{when}</time>'
        f'<span class="time-read">{item.read_time_minutes} dk okuma</span></div>'
        "</div></li>"
    )


def category_nav(base: str, active: str | None = None) -> str:
    links = [
        f'<a class="cat-pill{" is-active" if active is None else ""}" href="{attr(base)}/ui/">'
        "Tümü</a>"
    ]
    for slug, name in CANONICAL_CATEGORIES.items():
        cls = "cat-pill is-active" if slug == active else "cat-pill"
        current = ' aria-current="page"' if slug == active else ""
        links.append(
            f'<a class="{cls}" href="{attr(category_href(base, slug))}"{current}>{attr(name)}</a>'
        )
    return (
        '<nav class="category-navbar" aria-label="Haber kategorileri">'
        f'<div class="category-scroll">{"".join(links)}</div></nav>'
    )


def page_shell(*, head: str, base: str, body: str, active_category: str | None = None) -> str:
    year = datetime.now(UTC).year
    return f"""<!DOCTYPE html>
<html lang="tr" data-theme="dark" data-font-size="md">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#090c10" />
    {head}
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link rel="stylesheet" href="{FONTS_HREF}" />
    <link rel="stylesheet" href="{attr(base)}/ui/styles.css?v={ASSET_VERSION}" />
    <script src="{attr(base)}/ui/page.js?v={ASSET_VERSION}" defer></script>
  </head>
  <body class="page">
    <a class="skip-link" href="#icerik">İçeriğe geç</a>
    <header class="topbar">
      <div class="topbar-left">
        <a class="wordmark" href="{attr(base)}/ui/" aria-label="CuraNews ana sayfa">
          <span class="wordmark-mark" aria-hidden="true">C</span>
          <span class="wordmark-text">CuraNews</span>
        </a>
      </div>
      <a class="btn secondary btn-sm" href="{attr(base)}/ui/">Canlı akışa dön</a>
    </header>
    {category_nav(base, active_category)}
    <main id="icerik" class="page-main">
{body}
    </main>
    <footer class="footer">
      <div class="footer-inner">
        <p><strong>CuraNews</strong> · Haberler resmi RSS yayınlarından derlenir;
          tüm hakları ilgili yayıncılara aittir.</p>
        <p>
          <a href="{attr(base)}/ui/">Ana sayfa</a> ·
          <a href="{attr(base)}/rss.xml">RSS</a> ·
          <a href="{attr(base)}/sitemap.xml">Site haritası</a> · © {year}
        </p>
      </div>
    </footer>
  </body>
</html>
"""


def breadcrumb_ld(crumbs: Sequence[tuple[str, str]]) -> dict[str, Any]:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": url}
            for i, (name, url) in enumerate(crumbs, start=1)
        ],
    }
