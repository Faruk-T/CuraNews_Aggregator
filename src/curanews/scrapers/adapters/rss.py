"""Parse RSS 2.0 / Atom / RSS 1.0 XML into RawArticleDraft rows."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from lxml import etree

from curanews.domain.models import RawArticleDraft
from curanews.ingestion.cleaning import strip_html_tags
from curanews.nlp.categorizer import (
    calculate_read_time,
    categorize_text,
    detect_breaking_news,
)
from curanews.scrapers.adapters._paths import fixture_path
from curanews.scrapers.adapters.rss_catalog import RssFeed


def parse_feed_xml(xml: str | bytes, *, feed: RssFeed) -> list[RawArticleDraft]:
    """Map a syndication document to drafts; skip rows missing title or URL."""
    if isinstance(xml, str):
        xml = xml.encode("utf-8")
    try:
        root = etree.fromstring(xml)
    except etree.XMLSyntaxError:
        return []

    drafts: list[RawArticleDraft] = []
    for node in _item_nodes(root):
        draft = _draft_from_item(node, feed=feed)
        if draft is not None:
            drafts.append(draft)
    return drafts


def load_rss_fixture(*, feed: RssFeed | None = None) -> list[RawArticleDraft]:
    path = fixture_path("tests", "fixtures", "rss_sample.xml")
    sample_feed = feed or RssFeed(
        key="fixture_wire",
        publisher="CuraNews Fixture Wire",
        url="https://feeds.bbci.co.uk/news/world/rss.xml",
        category="world",
        language="en",
        host="feeds.bbci.co.uk",
    )
    return parse_feed_xml(path.read_text(encoding="utf-8"), feed=sample_feed)


def _item_nodes(root: etree._Element) -> list[etree._Element]:
    items = [el for el in root.iter() if _local(el.tag) in {"item", "entry"}]
    return items


def _draft_from_item(node: etree._Element, *, feed: RssFeed) -> RawArticleDraft | None:
    title = _first_text(node, "title")
    url = _link(node)
    if not title or not url:
        return None

    summary = _first_text(node, "description", "summary", "subtitle")
    encoded = _first_text(node, "encoded")  # content:encoded
    content_html = _first_text(node, "content") or encoded
    body_source = content_html or summary or title
    body = strip_html_tags(body_source)
    summary_clean = strip_html_tags(summary or body)[:500]
    if not body:
        return None

    published = _parse_datetime(
        _first_text(node, "pubdate", "published", "updated", "date")
    )
    category = _first_text(node, "category") or feed.category
    author = _first_text(node, "creator", "author", "name")
    if author and "<" in author:
        author = strip_html_tags(author)

    metadata: dict[str, Any] = {
        "provider": "rss",
        "feed_key": feed.key,
        "publisher": feed.publisher,
        "feed_url": feed.url,
    }

    image_url = _extract_image_url(node, content_html, summary)
    if image_url:
        metadata["image_url"] = image_url

    clean_title = strip_html_tags(title)
    cat_slug, cat_conf = categorize_text(
        title=clean_title,
        summary=summary_clean,
        body=body,
        default_category=category,
    )
    metadata["category_slug"] = cat_slug
    metadata["category_confidence"] = cat_conf
    metadata["is_breaking"] = detect_breaking_news(clean_title, summary_clean)
    metadata["read_time_minutes"] = calculate_read_time(body, summary_clean)

    # Use inferred category if feed category is missing or generic
    final_category = category
    if not final_category or final_category.lower() in {"world", "general", "turkey"}:
        final_category = cat_slug

    return RawArticleDraft(
        title=clean_title,
        url=url.strip(),
        content=body,
        summary=summary_clean,
        published_date=published or datetime.now(timezone.utc),
        source=f"{feed.key}:{feed.publisher}",
        category=final_category,
        author=author,
        language=feed.language,
        metadata=metadata,
    )


def _extract_image_url(node: etree._Element, *html_snippets: str | None) -> str | None:
    """Extract first valid image URL from enclosure, media tags, or embedded HTML."""
    for child in node:
        local = _local(child.tag)
        if local == "enclosure":
            url = (child.get("url") or "").strip()
            mime = (child.get("type") or "").lower()
            if url and (
                mime.startswith("image/")
                or any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"))
            ):
                return url
        elif local in {"content", "thumbnail"}:
            url = (child.get("url") or "").strip()
            if url and (url.startswith("http://") or url.startswith("https://")):
                return url

    img_pat = re.compile(r'<img[^>]+src=["\'](https?://[^"\'>\s]+)["\']', re.IGNORECASE)
    for snippet in html_snippets:
        if snippet:
            match = img_pat.search(snippet)
            if match:
                return match.group(1).strip()
    return None


def _link(node: etree._Element) -> str | None:
    for child in node:
        if _local(child.tag) != "link":
            continue
        href = (child.get("href") or "").strip()
        rel = (child.get("rel") or "alternate").lower()
        if href and rel in {"alternate", ""}:
            return href
        if href:
            return href
        text = (child.text or "").strip()
        if text:
            return text
    guid = _child(node, "guid")
    if guid is not None and (guid.get("isPermaLink") or "true").lower() == "true":
        text = (guid.text or "").strip()
        if text.startswith("http"):
            return text
    return None


def _first_text(node: etree._Element, *names: str) -> str | None:
    wanted = {name.lower() for name in names}
    for child in node:
        if _local(child.tag) not in wanted:
            continue
        text = _element_text(child)
        if text:
            return text
    return None


def _child(node: etree._Element, local_name: str) -> etree._Element | None:
    for child in node:
        if _local(child.tag) == local_name.lower():
            return child
    return None


def _element_text(node: etree._Element) -> str:
    chunks = [node.text or ""]
    for child in node:
        chunks.append(_element_text(child))
        chunks.append(child.tail or "")
    return "".join(chunks).strip()


def _local(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.split("}", 1)[-1].lower()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        pass
    cleaned = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
