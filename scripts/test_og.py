import httpx
import re

urls = [
    'https://www.aa.com.tr/tr/gundem/yaren-leylek-15inci-yilinda-goc-yolculuguna-basladi/4046892',
    'https://www.aa.com.tr/tr/gundem/hava-kuvvetleri-komutani-dalkiran-2026-2027-ucus-egitim-yilinin-ilk-ucusunu-yapti/4046893',
    'https://www.aljazeera.com/video/newsfeed/2026/9/3/train-crashes-into-truck-at-railway-crossing-in-gdansk-poland?traffic_source=rss'
]
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for u in urls:
    try:
        res = httpx.get(u, headers=headers, timeout=10.0, follow_redirects=True)
        m = re.search(r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'">]+)[\'"]', res.text, re.I)
        if not m:
            m = re.search(r'<meta[^>]+content=[\'"]([^\'">]+)[\'"][^>]+property=[\'"]og:image[\'"]', res.text, re.I)
        if not m:
            m = re.search(r'<meta[^>]+name=[\'"]twitter:image[\'"][^>]+content=[\'"]([^\'">]+)[\'"]', res.text, re.I)
        print(f"URL: {u[:50]}...")
        print(f"  REAL COVER PHOTO: {m.group(1) if m else 'NOT FOUND'}")
    except Exception as e:
        print(f"URL: {u[:50]}... ERR: {e}")
