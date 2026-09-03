"""Verify Day 22 features: Auth, Editor CMS, Comments, and Bookmarks."""

from __future__ import annotations

import httpx


def verify() -> None:
    client = httpx.Client(base_url="http://127.0.0.1:8002", timeout=10.0)

    # 1. Auth login
    login_payload = {"email": "editor@curanews.com", "password": "editor123"}
    r_login = client.post("/auth/login", json=login_payload)
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    user_data = r_login.json()
    token = user_data["access_token"]
    user_name = user_data["user"]["full_name"]
    print(f"[OK] 1. Login successful: {user_name} ({user_data['user']['role']})")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Editor article
    r_art = client.post(
        "/editor/articles",
        json={
            "title": "CuraNews Özel: Türkiye Yapay Zeka ve Geleceğin Meslekleri Raporu",
            "category": "teknoloji",
            "summary": "Üniversite ve sanayi işbirliğinde yapay zeka ekosistemi büyüyor.",
            "body": (
                "Türkiye genelinde yapay zeka ve veri mühendisliğinde rekor büyüme kaydedildi.\n\n"
                "Akademik araştırmalar sektörel üretim ve kamu dijitalleşmesiyle buluşuyor."
            ),
            "author_name": "Ahmet Yılmaz",
            "author_title": "Kıdemli Editör",
            "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        },
        headers=headers,
    )
    assert r_art.status_code == 200, f"Editor article failed: {r_art.text}"
    art = r_art.json()
    art_id = art["id"]
    print(f"[OK] 2. Editorial article published: '{art['title']}' (ID: {art_id})")

    # 3. Post a comment
    r_comm = client.post(
        f"/articles/{art_id}/comments",
        json={
            "content": "Üniversite bölüm başkanlığı jürisi adına bu çalışmayı takdir ediyoruz!",
            "author_name": "Prof. Dr. Bölüm Başkanı",
        },
    )
    assert r_comm.status_code == 200, f"Comment failed: {r_comm.text}"
    comm = r_comm.json()
    comm_id = comm["id"]
    print(f"[OK] 3. Comment posted: '{comm['content']}' by {comm['author_name']}")

    # 4. Like comment
    r_like = client.post(f"/comments/{comm_id}/like")
    assert r_like.status_code == 200, f"Like failed: {r_like.text}"
    print(f"[OK] 4. Comment liked: Total likes = {r_like.json()['likes']}")

    # 5. Bookmark article
    bm_payload = {"article_id": art_id, "user_id": "demo-editor"}
    r_bm = client.post("/bookmarks", json=bm_payload, headers=headers)
    assert r_bm.status_code == 200, f"Bookmark failed: {r_bm.text}"
    print(f"[OK] 5. Article bookmarked: is_bookmarked = {r_bm.json()['is_bookmarked']}")

    # 6. List bookmarks
    r_bmlist = client.get("/bookmarks?user_id=demo-editor", headers=headers)
    assert r_bmlist.status_code == 200
    assert r_bmlist.json()["total"] >= 1
    print(f"[OK] 6. Bookmarks listed: Total {r_bmlist.json()['total']} items")

    print("\n[SUCCESS] ALL DAY 22 FEATURES VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    verify()
