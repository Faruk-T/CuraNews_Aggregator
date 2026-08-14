"""Verify User A vs User B curation ranking differs (Issue #15 / G15).

Usage::

    poetry run python scripts/seed_demo_users.py
    poetry run python scripts/verify_curation.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from curanews.db.models import Article
from curanews.db.session import get_session_factory
from curanews.db.user_repository import UserRepository
from curanews.logging_setup import setup_logging
from curanews.nlp.curation import CurationEngine
from curanews.privacy.pii import scrub_pii


PII_FIXTURE = (
    "Contact reporter@example.com or @newsdesk at +1 (212) 555-0199 for comment."
)


def main() -> int:
    setup_logging()
    factory = get_session_factory()
    session = factory()
    try:
        users = UserRepository(session)
        user_a = users.get_by_external_key("demo-user-a")
        user_b = users.get_by_external_key("demo-user-b")
        if user_a is None or user_b is None:
            print("demo users missing — run seed_demo_users.py first", file=sys.stderr)
            return 1

        candidates = list(session.scalars(select(Article)).all())
        if len(candidates) < 2:
            print("need at least 2 articles — run seed_demo_users.py", file=sys.stderr)
            return 1

        engine = CurationEngine(session)
        now = datetime(2026, 8, 14, 18, 0, tzinfo=timezone.utc)
        ranked_a = engine.rank(user_a.id, candidates, now=now, top_k=5)
        ranked_b = engine.rank(user_b.id, candidates, now=now, top_k=5)

        def _rows(scored: list) -> list[dict]:
            return [
                {
                    "rank": i + 1,
                    "title": s.article.title,
                    "score": round(s.score, 4),
                    "interest": round(s.interest, 4),
                    "freshness": round(s.freshness, 4),
                    "penalty": round(s.penalty, 4),
                }
                for i, s in enumerate(scored)
            ]

        order_a = [s.article.title for s in ranked_a]
        order_b = [s.article.title for s in ranked_b]
        scrubbed = scrub_pii(PII_FIXTURE)

        payload = {
            "user_a": {
                "external_key": user_a.external_key,
                "profile": sorted(users.entity_profile(user_a.id)),
                "feed": _rows(ranked_a),
            },
            "user_b": {
                "external_key": user_b.external_key,
                "profile": sorted(users.entity_profile(user_b.id)),
                "feed": _rows(ranked_b),
            },
            "ranking_differs": order_a != order_b,
            "pii_fixture": PII_FIXTURE,
            "pii_scrubbed": scrubbed,
            "pii_ok": (
                "reporter@example.com" not in scrubbed
                and "@newsdesk" not in scrubbed
                and "555-0199" not in scrubbed
            ),
        }
        print(json.dumps(payload, indent=2))
        if not payload["ranking_differs"]:
            print("expected different ranking for user A vs B", file=sys.stderr)
            return 1
        if not payload["pii_ok"]:
            print("PII scrub failed", file=sys.stderr)
            return 1
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"verify curation failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
