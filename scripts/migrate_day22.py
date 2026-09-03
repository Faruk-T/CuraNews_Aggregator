"""Migration helper to add Day 22 columns to Postgres users table."""

from __future__ import annotations

from sqlalchemy import text

from curanews.db.session import get_engine


def migrate() -> None:
    engine = get_engine()
    with engine.connect() as conn:
        for stmt in [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(200);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(120);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(32) DEFAULT 'reader';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSON DEFAULT '{}';",
        ]:
            conn.execute(text(stmt))
        conn.commit()
        print("Users table successfully migrated for Day 22!")


if __name__ == "__main__":
    migrate()
