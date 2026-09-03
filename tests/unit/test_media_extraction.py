"""Unit tests for media extraction and source logo badges (Day 21)."""

from __future__ import annotations

from lxml import etree

from curanews.api.services import get_source_logo_svg
from curanews.scrapers.adapters.rss import _extract_image_url


def test_extract_image_from_enclosure() -> None:
    xml = """
    <item>
        <title>Örnek Haber</title>
        <link>https://example.com/news/1</link>
        <enclosure url="https://images.example.com/cover.jpg" type="image/jpeg" length="12345" />
    </item>
    """
    node = etree.fromstring(xml.strip().encode("utf-8"))
    img = _extract_image_url(node)
    assert img == "https://images.example.com/cover.jpg"


def test_extract_image_from_media_content() -> None:
    xml = """
    <item xmlns:media="http://search.yahoo.com/mrss/">
        <title>Örnek Haber</title>
        <link>https://example.com/news/2</link>
        <media:content url="https://images.example.com/banner.webp" medium="image" />
    </item>
    """
    node = etree.fromstring(xml.strip().encode("utf-8"))
    img = _extract_image_url(node)
    assert img == "https://images.example.com/banner.webp"


def test_extract_image_from_embedded_html() -> None:
    xml = """
    <item>
        <title>Örnek Haber</title>
        <link>https://example.com/news/3</link>
    </item>
    """
    html_desc = (
        '<p>Detaylı haber metni '
        '<img src="https://cdn.example.com/inline.png" alt="görsel" /></p>'
    )
    node = etree.fromstring(xml.strip().encode("utf-8"))
    img = _extract_image_url(node, html_desc)
    assert img == "https://cdn.example.com/inline.png"


def test_get_source_logo_svg() -> None:
    logo_aa = get_source_logo_svg("Anadolu Ajansı")
    assert "data:image/svg+xml;utf8," in logo_aa
    assert "AA" in logo_aa
    assert "#003B70" in logo_aa

    logo_trt = get_source_logo_svg("TRT Haber")
    assert "TRT" in logo_trt
    assert "#C8102E" in logo_trt

    logo_generic = get_source_logo_svg("Özel Yerel Haber")
    assert "data:image/svg+xml;utf8," in logo_generic
