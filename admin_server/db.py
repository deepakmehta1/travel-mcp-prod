import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/travel"
        )
        _engine = create_engine(db_url, pool_pre_ping=True)
    return _engine


def execute_query(query: str, params: dict | None = None):
    """Execute a query and return results as list of dicts"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        if result.returns_rows:
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        conn.commit()
        return []
