"""Sitemap, robots.txt, RSS syndication and ads.txt (Day 23)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
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

Sitemap: {base}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain; charset=utf-8")


@router.get("/sitemap.xml", response_class=Response)
def get_sitemap_xml(request: Request, session: Session = Depends(get_db)) -> Response:
    """Only URLs served by this site; publisher URLs belong in their own sitemaps."""
    base = public_base_url(request)
    now = datetime.now(UTC).isoformat(timespec="seconds")

    entries = [(f"{base}/ui/", now, "hourly", "1.0")]
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
        items.append(
            f"""    <item>
      <title>{escape(art.title)}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <description>{escape(clip(art.summary or art.title, 400))}</description>
      <category>{escape(art.category or "gundem")}</category>
      <source url="{escape(base)}/rss.xml">{source}</source>
      <pubDate>{_stamp(art).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>{enclosure}
    </item>"""
        )

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{SITE_NAME}</title>
    <link>{escape(base)}/ui/</link>
    <description>{escape(SITE_DESCRIPTION)}</description>
    <language>tr</language>
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
