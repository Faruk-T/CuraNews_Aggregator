"""SEO, Sitemap, Robots.txt, RSS Syndication and IAB ads.txt router (Day 23)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Response
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.config import get_settings
from curanews.db.models import Article

router = APIRouter(tags=["seo"])


def _get_base_url() -> str:
    domain = os.environ.get("DOMAIN_NAME", "curanews.com").strip()
    is_local = domain in ("localhost", "127.0.0.1") or domain.startswith("127.0.0.1:")
    proto = "http" if is_local else "https"
    return f"{proto}://{domain}"


@router.get("/robots.txt", response_class=Response)
def get_robots_txt() -> Response:
    """Return standard robots.txt for search engine crawlers."""
    base_url = _get_base_url()
    content = f"""# CuraNews Aggregator Robots.txt (Day 23)
User-agent: *
Allow: /
Allow: /ui/
Allow: /sitemap.xml
Allow: /rss.xml
Allow: /ads.txt
Disallow: /api/auth/
Disallow: /api/reads/
Disallow: /editor/

# Search Engine Crawlers
User-agent: Googlebot
Allow: /

User-agent: Googlebot-News
Allow: /

User-agent: Bingbot
Allow: /

User-agent: YandexBot
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain; charset=utf-8")


@router.get("/sitemap.xml", response_class=Response)
def get_sitemap_xml(session: Session = Depends(get_db)) -> Response:
    """Generate dynamic XML Sitemap for Google Search Console and web indexers."""
    base_url = _get_base_url()
    now_iso = datetime.now(UTC).strftime("%Y-%m-%d")

    categories = [
        ("gundem", "0.8"),
        ("ekonomi", "0.8"),
        ("teknoloji", "0.8"),
        ("spor", "0.7"),
        ("saglik", "0.7"),
        ("dunya", "0.7"),
        ("politika", "0.7"),
    ]

    urls = [
        f"""  <url>
    <loc>{base_url}/</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>"""
    ]

    for cat_slug, priority in categories:
        urls.append(
            f"""  <url>
    <loc>{base_url}/ui/?category={cat_slug}</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>{priority}</priority>
  </url>"""
        )

    # Fetch latest 200 articles
    articles = list(
        session.scalars(
            select(Article).order_by(desc(Article.published_at)).limit(200)
        ).all()
    )

    for art in articles:
        mod_date = (art.published_at or art.scraped_at or datetime.now(UTC)).strftime("%Y-%m-%d")
        safe_loc = escape(art.url)
        urls.append(
            f"""  <url>
    <loc>{safe_loc}</loc>
    <lastmod>{mod_date}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>"""
        )

    xml_body = "\n".join(urls)
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml_body}
</urlset>"""

    return Response(content=sitemap_content, media_type="application/xml; charset=utf-8")


@router.get("/rss.xml", response_class=Response)
def get_rss_xml(session: Session = Depends(get_db)) -> Response:
    """Generate valid RSS 2.0 feed for news aggregators and Google News."""
    base_url = _get_base_url()
    settings = get_settings()

    articles = list(
        session.scalars(
            select(Article).order_by(desc(Article.published_at)).limit(50)
        ).all()
    )

    items = []
    for art in articles:
        pub_date = (art.published_at or art.scraped_at or datetime.now(UTC)).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        safe_title = escape(art.title)
        safe_desc = escape(art.summary or art.title)
        safe_link = escape(art.url)
        safe_cat = escape(art.category or "gundem")

        meta = art.raw_metadata or {}
        enclosure = ""
        img_url = meta.get("image_url")
        if img_url:
            enclosure = f'<enclosure url="{escape(img_url)}" type="image/jpeg" />'

        items.append(
            f"""    <item>
      <title>{safe_title}</title>
      <link>{safe_link}</link>
      <description>{safe_desc}</description>
      <category>{safe_cat}</category>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="false">{art.id}</guid>
      {enclosure}
    </item>"""
        )

    items_str = "\n".join(items)
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(settings.app_name)}</title>
    <link>{base_url}/</link>
    <description>Akıllı Haber Kürasyonu ve Editör Masası</description>
    <language>tr</language>
    <atom:link href="{base_url}/rss.xml" rel="self" type="application/rss+xml" />
{items_str}
  </channel>
</rss>"""

    return Response(content=rss_content, media_type="application/rss+xml; charset=utf-8")


@router.get("/ads.txt", response_class=Response)
def get_ads_txt() -> Response:
    """Return IAB compliant ads.txt for Google AdSense & programmatic ad verification."""
    adsense_id = os.environ.get("ADSENSE_PUB_ID", "pub-8573920194827104").strip()
    content = f"""# CuraNews Aggregator IAB ads.txt (Day 23)
# https://iabtechlab.com/ads-txt/
google.com, {adsense_id}, DIRECT, f08c47fec0942fa0
"""
    return Response(content=content, media_type="text/plain; charset=utf-8")
