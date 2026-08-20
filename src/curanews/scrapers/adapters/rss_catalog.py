"""Public RSS catalog — licensed syndication feeds, not HTML scraping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RssFeed:
    """One publisher RSS/Atom endpoint that CuraNews is allowed to fetch."""

    key: str
    publisher: str
    url: str
    category: str
    language: str
    host: str


def _feed(
    key: str,
    publisher: str,
    url: str,
    *,
    category: str,
    language: str,
    host: str,
) -> RssFeed:
    return RssFeed(
        key=key,
        publisher=publisher,
        url=url,
        category=category,
        language=language,
        host=host,
    )


# Hosts must stay in SCRAPE_ALLOWLIST_HOSTS. Feeds are official RSS/Atom
# endpoints. TRT Spor does not publish a public RSS; TRT Haber + NTV Spor
# cover the same sports desk ethically.
DEFAULT_RSS_FEEDS: tuple[RssFeed, ...] = (
    _feed(
        "bbc_world",
        "BBC News",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        category="world",
        language="en",
        host="feeds.bbci.co.uk",
    ),
    _feed(
        "bbc_turkish",
        "BBC Türkçe",
        "https://feeds.bbci.co.uk/turkce/rss.xml",
        category="world",
        language="tr",
        host="feeds.bbci.co.uk",
    ),
    _feed(
        "guardian_world",
        "The Guardian",
        "https://www.theguardian.com/world/rss",
        category="world",
        language="en",
        host="www.theguardian.com",
    ),
    _feed(
        "npr_news",
        "NPR",
        "https://feeds.npr.org/1001/rss.xml",
        category="general",
        language="en",
        host="feeds.npr.org",
    ),
    _feed(
        "aljazeera_english",
        "Al Jazeera",
        "https://www.aljazeera.com/xml/rss/all.xml",
        category="world",
        language="en",
        host="www.aljazeera.com",
    ),
    _feed(
        "aa_guncel",
        "Anadolu Ajansı",
        "https://www.aa.com.tr/tr/rss/default?cat=guncel",
        category="world",
        language="tr",
        host="www.aa.com.tr",
    ),
    _feed(
        "dw_turkish",
        "DW Türkçe",
        "https://rss.dw.com/xml/rss-tur-all",
        category="world",
        language="tr",
        host="rss.dw.com",
    ),
    _feed(
        "trt_haber",
        "TRT Haber",
        "https://www.trthaber.com/sondakika.rss",
        category="turkey",
        language="tr",
        host="www.trthaber.com",
    ),
    _feed(
        "ahaber_home",
        "A Haber",
        "https://www.ahaber.com.tr/rss/anasayfa.xml",
        category="turkey",
        language="tr",
        host="www.ahaber.com.tr",
    ),
    _feed(
        "ahaber_spor",
        "A Haber Spor",
        "https://www.ahaber.com.tr/rss/spor.xml",
        category="sports",
        language="tr",
        host="www.ahaber.com.tr",
    ),
    _feed(
        "ntv_gundem",
        "NTV",
        "https://www.ntv.com.tr/gundem.rss",
        category="turkey",
        language="tr",
        host="www.ntv.com.tr",
    ),
    _feed(
        "ntv_spor",
        "NTV Spor",
        "https://www.ntv.com.tr/sporskor.rss",
        category="sports",
        language="tr",
        host="www.ntv.com.tr",
    ),
    _feed(
        "cnnturk_spor",
        "CNN Türk Spor",
        "https://www.cnnturk.com/feed/rss/spor/news",
        category="sports",
        language="tr",
        host="www.cnnturk.com",
    ),
    _feed(
        "hurriyet_spor",
        "Hürriyet Spor",
        "https://www.hurriyet.com.tr/rss/spor",
        category="sports",
        language="tr",
        host="www.hurriyet.com.tr",
    ),
    _feed(
        "milliyet_spor",
        "Milliyet Spor",
        "https://www.milliyet.com.tr/rss/rssNew/sporRss.xml",
        category="sports",
        language="tr",
        host="www.milliyet.com.tr",
    ),
    _feed(
        "haberturk",
        "Habertürk",
        "https://www.haberturk.com/rss",
        category="turkey",
        language="tr",
        host="www.haberturk.com",
    ),
)

RSS_ALLOWLIST_HOSTS: tuple[str, ...] = tuple(sorted({feed.host for feed in DEFAULT_RSS_FEEDS}))
