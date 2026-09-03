from curanews.db.session import get_engine
from sqlalchemy.orm import Session
from curanews.db.models import Article, Source

s = Session(get_engine())
titles = ['Train crashes', 'Funeral held', 'Hava Kuvvetleri', 'Yaren leylek', 'Fenerbahçe']
for t in titles:
    arts = s.query(Article).filter(Article.title.ilike(f'%{t}%')).all()
    for a in arts:
        meta = a.raw_metadata or {}
        src = s.get(Source, a.source_id)
        print(f"TITLE: {a.title[:60]}")
        print(f"  SOURCE: {src.name if src else None} | URL: {a.url}")
        print(f"  IMG in meta: {meta.get('image_url')}")
        print(f"  RAW_META keys: {list(meta.keys())}")
s.close()
