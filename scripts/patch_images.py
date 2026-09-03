from curanews.db.session import get_engine
from sqlalchemy.orm import Session
from curanews.db.models import Article
from curanews.api.services import CATEGORY_FALLBACK_IMAGES

s = Session(get_engine())
arts = s.query(Article).all()
updated = 0
for a in arts:
    meta = dict(a.raw_metadata or {})
    if not meta.get('image_url'):
        cat = (a.category or 'gundem').lower()
        img = CATEGORY_FALLBACK_IMAGES.get(cat, 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&auto=format&fit=crop')
        meta['image_url'] = img
        a.raw_metadata = meta
        updated += 1
s.commit()
print(f"Success: Updated {updated} articles with category fallback imagery.")
s.close()
