"""Extract official real cover photos (og:image / twitter:image) for all articles."""
import asyncio
import re
import httpx
from curanews.db.session import get_engine
from sqlalchemy.orm import Session
from curanews.db.models import Article

OG_PATTERNS = [
    re.compile(r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'">]+)[\'"]', re.I),
    re.compile(r'<meta[^>]+content=[\'"]([^\'">]+)[\'"][^>]+property=[\'"]og:image[\'"]', re.I),
    re.compile(r'<meta[^>]+name=[\'"]twitter:image[\'"][^>]+content=[\'"]([^\'">]+)[\'"]', re.I),
    re.compile(r'<meta[^>]+content=[\'"]([^\'">]+)[\'"][^>]+name=[\'"]twitter:image[\'"]', re.I),
    re.compile(r'<meta[^>]+itemprop=[\'"]image[\'"][^>]+content=[\'"]([^\'">]+)[\'"]', re.I),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

async def fetch_cover(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        res = await client.get(url, headers=HEADERS, timeout=8.0, follow_redirects=True)
        if res.status_code >= 400:
            return None
        text = res.text
        for pat in OG_PATTERNS:
            m = pat.search(text)
            if m:
                img = m.group(1).strip()
                if img.startswith("http://") or img.startswith("https://"):
                    # Avoid 1x1 tracking pixels or generic favicons
                    if not any(bad in img.lower() for bad in ["1x1", "favicon", "logo.png", "blank.gif"]):
                        return img
    except Exception:
        pass
    return None

async def main():
    engine = get_engine()
    session = Session(engine)
    articles = session.query(Article).order_by(Article.scraped_at.desc()).all()
    print(f"Scanning {len(articles)} articles for real official news cover photos...")

    targets = [
        a for a in articles 
        if "unsplash.com" in ((a.raw_metadata or {}).get("image_url") or "") 
        or not (a.raw_metadata or {}).get("image_url")
    ]
    print(f"Found {len(targets)} articles needing authentic cover photos.")

    updated_count = 0
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    async with httpx.AsyncClient(limits=limits) as client:
        batch_size = 15
        for i in range(0, len(targets), batch_size):
            batch = targets[i:i+batch_size]
            tasks = [fetch_cover(client, a.url) for a in batch]
            results = await asyncio.gather(*tasks)
            for a, img in zip(batch, results):
                if img:
                    meta = dict(a.raw_metadata or {})
                    meta["image_url"] = img
                    meta["has_real_cover"] = True
                    a.raw_metadata = meta
                    updated_count += 1
                    safe_title = a.title[:45].encode('ascii', 'replace').decode()
                    print(f"  + REAL COVER: {safe_title} -> {img[:60]}...")
            session.commit()
            print(f"Progress: {min(i + batch_size, len(targets))}/{len(targets)} (Updated: {updated_count})")

    session.close()
    print(f"\nDone! Successfully updated {updated_count} articles with authentic news cover photos!")

if __name__ == "__main__":
    asyncio.run(main())
