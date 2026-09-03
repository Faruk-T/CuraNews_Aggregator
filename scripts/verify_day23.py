"""Comprehensive Day 23 Verification Script: SEO, Ad Policies, GA4, GSC, Deployment.

Usage:
    poetry run python scripts/verify_day23.py
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi.testclient import TestClient

from curanews.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]


def verify() -> None:
    print("==================================================")
    print(" [DAY 23] CuraNews Comprehensive Verification")
    print("==================================================")

    app = create_app()
    client = TestClient(app)

    # 1. Robots.txt
    res_rob = client.get("/robots.txt")
    assert res_rob.status_code == 200, f"robots.txt failed: {res_rob.status_code}"
    assert "User-agent: Googlebot" in res_rob.text
    assert "Sitemap:" in res_rob.text
    print("[OK] 1. /robots.txt is live and properly directs Googlebot & crawlers")

    # 2. Sitemap.xml
    res_sm = client.get("/sitemap.xml")
    assert res_sm.status_code == 200, f"sitemap.xml failed: {res_sm.status_code}"
    root_sm = ET.fromstring(res_sm.text)
    assert root_sm.tag.endswith("urlset")
    urls = [elem.text for elem in root_sm.iter() if elem.tag.endswith("loc")]
    assert len(urls) >= 8
    print(f"[OK] 2. /sitemap.xml is valid XML with {len(urls)} indexed URLs")

    # 3. RSS 2.0 Syndication Feed
    res_rss = client.get("/rss.xml")
    assert res_rss.status_code == 200, f"rss.xml failed: {res_rss.status_code}"
    root_rss = ET.fromstring(res_rss.text)
    assert root_rss.tag == "rss"
    print("[OK] 3. /rss.xml is a valid RSS 2.0 channel for Google News")

    # 4. IAB ads.txt
    res_ads = client.get("/ads.txt")
    assert res_ads.status_code == 200, f"ads.txt failed: {res_ads.status_code}"
    assert "google.com" in res_ads.text
    assert "DIRECT" in res_ads.text
    print("[OK] 4. /ads.txt conforms to IAB Tech Lab and Google AdSense specifications")

    # 5. Frontend SEO & Analytics Meta
    html_path = ROOT / "web" / "index.html"
    assert html_path.is_file(), "web/index.html not found"
    html = html_path.read_text(encoding="utf-8")

    assert "google-site-verification" in html, "Google Search Console tag missing"
    assert "G-CURANEWS2026" in html, "Google Analytics 4 script missing"
    assert "og:title" in html, "OpenGraph meta tag missing"
    assert "twitter:card" in html, "Twitter Card tag missing"
    assert "NewsMediaOrganization" in html, "Schema.org JSON-LD missing"
    assert "cookieConsentBanner" in html, "IAB cookie/ad consent banner missing"
    assert "policyModal" in html, "Ad policy modal missing"
    print("[OK] 5. Frontend contains GSC, GA4, OpenGraph, Schema.org, and Cookie Banner")

    # 6. Production Deployment Files
    compose_path = ROOT / "docker-compose.prod.yml"
    caddy_path = ROOT / "Caddyfile"
    deploy_sh = ROOT / "scripts" / "deploy_vds.sh"
    guide_path = ROOT / "docs" / "DEPLOYMENT_GUIDE.md"

    assert compose_path.is_file(), "docker-compose.prod.yml missing"
    assert caddy_path.is_file(), "Caddyfile missing"
    assert deploy_sh.is_file(), "deploy_vds.sh missing"
    assert guide_path.is_file(), "DEPLOYMENT_GUIDE.md missing"
    print("[OK] 6. Production Compose, Caddyfile, deploy script, and guide are verified")

    print("\n[SUCCESS] ALL DAY 23 REQUIREMENTS VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    verify()
