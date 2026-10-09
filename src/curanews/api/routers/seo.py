"""Sitemap, robots.txt, RSS syndication and ads.txt (Day 23)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.api.urls import article_path, public_base_url
from curanews.config import get_settings
from curanews.db.models import Article
from curanews.nlp.categorizer import CANONICAL_CATEGORIES
from curanews.timeutil import correct_future_timestamp
from curanews.web.render import SITE_DESCRIPTION, SITE_NAME, clip

router = APIRouter(tags=["seo"])

SITEMAP_ARTICLE_LIMIT = 5000
NEWS_SITEMAP_HOURS = 48
NEWS_SITEMAP_LIMIT = 1000
RSS_ITEM_LIMIT = 50
_ADSENSE_ID = re.compile(r"pub-\d{10,20}")


def _stamp(article: Any) -> datetime:
    value = correct_future_timestamp(article.published_at) or article.scraped_at
    return value if value.tzinfo else value.replace(tzinfo=UTC)


@router.get("/robots.txt", response_class=Response)
def get_robots_txt(request: Request) -> Response:
    base = public_base_url(request)
    content = f"""User-agent: *
Allow: /
Disallow: /auth/
Disallow: /editor/
Disallow: /reads
Disallow: /bookmarks
Disallow: /feed

User-agent: Googlebot-News
Allow: /

Sitemap: {base}/sitemap.xml
Sitemap: {base}/news-sitemap.xml
"""
    return Response(content=content, media_type="text/plain; charset=utf-8")


@router.get("/sitemap.xml", response_class=Response)
def get_sitemap_xml(request: Request, session: Session = Depends(get_db)) -> Response:
    """Only URLs served by this site; publisher URLs belong in their own sitemaps."""
    base = public_base_url(request)
    now = datetime.now(UTC).isoformat(timespec="seconds")

    entries = [
        (f"{base}/ui/", now, "hourly", "1.0"),
        (f"{base}/kunye", now, "monthly", "0.4"),
    ]
    entries += [(f"{base}/kategori/{slug}", now, "hourly", "0.8") for slug in CANONICAL_CATEGORIES]
    articles = session.execute(
        select(Article.id, Article.title, Article.published_at, Article.scraped_at)
        .order_by(desc(Article.published_at).nulls_last())
        .limit(SITEMAP_ARTICLE_LIMIT)
    ).all()
    entries += [
        (
            f"{base}/{article_path(art.id, art.title)}",
            _stamp(art).isoformat(timespec="seconds"),
            "daily",
            "0.6",
        )
        for art in articles
    ]

    body = "\n".join(
        f"  <url><loc>{escape(loc)}</loc><lastmod>{mod}</lastmod>"
        f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>"
        for loc, mod, freq, prio in entries
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>"
    )
    return Response(
        content=xml,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=600"},
    )


@router.get("/news-sitemap.xml", response_class=Response)
def get_news_sitemap_xml(request: Request, session: Session = Depends(get_db)) -> Response:
    """Google News sitemap: articles published in the last two days."""
    base = public_base_url(request)
    cutoff = datetime.now(UTC) - timedelta(hours=NEWS_SITEMAP_HOURS)
    articles = session.execute(
        select(Article.id, Article.title, Article.published_at, Article.scraped_at)
        .where(Article.published_at >= cutoff)
        .order_by(desc(Article.published_at))
        .limit(NEWS_SITEMAP_LIMIT)
    ).all()

    rows = []
    for art in articles:
        loc = escape(f"{base}/{article_path(art.id, art.title)}")
        published = _stamp(art).isoformat(timespec="seconds").replace("+00:00", "Z")
        title = escape(art.title or "")
        rows.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            "    <news:news>\n"
            "      <news:publication>\n"
            f"        <news:name>{escape(SITE_NAME)}</news:name>\n"
            "        <news:language>tr</news:language>\n"
            "      </news:publication>\n"
            f"      <news:publication_date>{published}</news:publication_date>\n"
            f"      <news:title>{title}</news:title>\n"
            "    </news:news>\n"
            "  </url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + ("\n".join(rows) + "\n" if rows else "")
        + "</urlset>"
    )
    return Response(
        content=xml,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/rss.xml", response_class=Response)
def get_rss_xml(request: Request, session: Session = Depends(get_db)) -> Response:
    base = public_base_url(request)
    articles = session.scalars(
        select(Article).order_by(desc(Article.published_at).nulls_last()).limit(RSS_ITEM_LIMIT)
    ).all()

    items = []
    for art in articles:
        link = escape(f"{base}/{article_path(art.id, art.title)}")
        meta = art.raw_metadata or {}
        enclosure = ""
        img_url = meta.get("image_url")
        if isinstance(img_url, str) and img_url.startswith(("http://", "https://")):
            enclosure = (
                f'\n      <enclosure url="{escape(img_url)}" type="image/jpeg" length="0" />'
            )
        source = escape(str(meta.get("publisher") or SITE_NAME))
        origin = art.url if str(art.url).startswith(("http://", "https://")) else f"{base}/rss.xml"
        items.append(
            f"""    <item>
      <title>{escape(art.title)}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <description>{escape(clip(art.summary or art.title, 400))}</description>
      <category>{escape(art.category or "gundem")}</category>
      <source url="{escape(origin)}">{source}</source>
      <pubDate>{_stamp(art).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>{enclosure}
    </item>"""
        )

    built = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{SITE_NAME}</title>
    <link>{escape(base)}/ui/</link>
    <description>{escape(SITE_DESCRIPTION)}</description>
    <language>tr</language>
    <lastBuildDate>{built}</lastBuildDate>
    <ttl>15</ttl>
    <atom:link href="{escape(base)}/rss.xml" rel="self" type="application/rss+xml" />
{chr(10).join(items)}
  </channel>
</rss>"""
    return Response(
        content=rss,
        media_type="application/rss+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/ads.txt", response_class=Response)
def get_ads_txt() -> Response:
    """IAB ads.txt; served only once a real AdSense publisher id is configured."""
    pub_id = get_settings().adsense_pub_id.strip().removeprefix("ca-")
    if not _ADSENSE_ID.fullmatch(pub_id):
        return Response(
            content="# ads.txt: no authorized sellers configured\n",
            status_code=404,
            media_type="text/plain; charset=utf-8",
        )
    content = f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"
    return Response(content=content, media_type="text/plain; charset=utf-8")
