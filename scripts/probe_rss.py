"""Probe candidate RSS URLs (operator helper)."""

from __future__ import annotations

import httpx

URLS = [
    "https://www.ahaber.com.tr/rss/anasayfa.xml",
    "https://www.ahaber.com.tr/rss/spor.xml",
    "https://www.ntv.com.tr/spor.rss",
    "https://www.ntv.com.tr/dunya.rss",
    "https://www.cnnturk.com/feed/rss/spor/news",
    "https://www.hurriyet.com.tr/rss/spor",
    "https://www.trthaber.com/sondakika.rss",
    "https://www.trtspor.com.tr/rss",
    "https://www.fanatik.com.tr/rss",
    "https://rss.dw.com/xml/rss-tur-all",
    "https://www.haberturk.com/rss",
    "https://www.sozcu.com.tr/feed/",
    "https://www.ntv.com.tr/gundem.rss",
    "https://www.ntv.com.tr/sporskor.rss",
    "https://www.fanatik.com.tr/rss/anasayfa",
    "https://www.trthaber.com/spor.rss",
    "https://www.milliyet.com.tr/rss/rssNew/sporRss.xml",
]

HEADERS = {
    "User-Agent": "CuraNewsBot/0.1 (+https://github.com/Faruk-T/CuraNews_Aggregator)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def main() -> None:
    with httpx.Client(timeout=12.0, follow_redirects=True, headers=HEADERS) as client:
        for url in URLS:
            try:
                response = client.get(url)
                snippet = response.text[:70].replace("\n", " ")
                print(f"{response.status_code}\t{len(response.text):6d}\t{url}\t{snippet}")
            except Exception as exc:  # noqa: BLE001
                print(f"ERR\t{url}\t{exc}")


if __name__ == "__main__":
    main()
