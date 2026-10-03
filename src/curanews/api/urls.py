"""Public URL helpers: site base, article permalinks and user-supplied URL validation."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from starlette.requests import Request

from curanews.config import get_settings

_TR_FOLD = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "Ş": "s",
        "ğ": "g",
        "Ğ": "g",
        "ç": "c",
        "Ç": "c",
        "ö": "o",
        "Ö": "o",
        "ü": "u",
        "Ü": "u",
    }
)
_YOUTUBE_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_VIMEO_ID = re.compile(r"\d{6,12}")


def slugify(text: str, *, max_length: int = 80) -> str:
    folded = unicodedata.normalize("NFKD", text.translate(_TR_FOLD))
    ascii_only = folded.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0] or slug[:max_length]
    return slug or "haber"


def article_path(article_id: UUID | str, title: str) -> str:
    """Site-relative permalink, e.g. ``haber/<uuid>/<slug>`` (no leading slash)."""
    return f"haber/{article_id}/{slugify(title)}"


def public_base_url(request: Request | None = None) -> str:
    """Absolute site root without trailing slash, including any reverse-proxy prefix."""
    configured = get_settings().public_base_url.strip().rstrip("/")
    if configured:
        return configured
    domain = os.environ.get("DOMAIN_NAME", "").strip()
    if domain and domain not in {"localhost", "127.0.0.1"}:
        return f"https://{domain}"
    if request is not None:
        prefix = request.headers.get("x-forwarded-prefix", "").rstrip("/")
        return f"{str(request.base_url).rstrip('/')}{prefix}"
    return "http://localhost:8000"


def base_path(request: Request | None = None) -> str:
    """Path component of the public base (``/curanews`` or empty)."""
    return urlparse(public_base_url(request)).path.rstrip("/")


def safe_http_url(value: Any, *, max_length: int = 2048) -> str | None:
    """Return the URL only when it is an absolute http(s) URL; blocks javascript:/data:."""
    if not value:
        return None
    url = str(value).strip()
    if len(url) > max_length:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return url


def video_embed_url(value: Any) -> str | None:
    """Map YouTube/Vimeo links to a privacy-friendly embed URL; anything else is rejected."""
    url = safe_http_url(value)
    if url is None:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    video_id: str | None = None
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "youtube-nocookie.com"}:
        if parsed.path == "/watch":
            video_id = (parse_qs(parsed.query).get("v") or [""])[0]
        elif parsed.path.startswith(("/embed/", "/shorts/", "/live/")):
            video_id = parsed.path.split("/")[2]
    elif host in {"vimeo.com", "player.vimeo.com"}:
        candidate = parsed.path.strip("/").split("/")[-1]
        if _VIMEO_ID.fullmatch(candidate):
            return f"https://player.vimeo.com/video/{candidate}"
        return None
    if video_id and _YOUTUBE_ID.fullmatch(video_id):
        return f"https://www.youtube-nocookie.com/embed/{video_id}"
    return None
