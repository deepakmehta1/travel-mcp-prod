import logging
from typing import Optional

from psycopg.types.json import Json
from psycopg_pool import ConnectionPool

try:
    from .config import build_conninfo, get_settings
except ImportError:
    from config import build_conninfo, get_settings

logger = logging.getLogger("server")

_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        conninfo = build_conninfo(settings)
        _pool = ConnectionPool(
            conninfo=conninfo,
            min_size=settings.pool_min_size,
            max_size=settings.pool_max_size,
            open=True,
        )
        logger.info(
            "Postgres pool initialized",
            extra={"min_size": settings.pool_min_size, "max_size": settings.pool_max_size},
        )
    return _pool


def init_db() -> None:
    schema_sql = """
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS tours (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        base_price INTEGER NOT NULL,
        nights INTEGER NOT NULL,
        destination TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        tour_code TEXT NOT NULL REFERENCES tours(code),
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        total_price INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            cur.execute("SELECT COUNT(*) AS count FROM customers")
            customers_count = cur.fetchone()[0]
            if customers_count == 0:
                cur.execute(
                    """
                    INSERT INTO customers (name, email, phone, preferences)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        "Deepak Mehta",
                        "deepak@example.com",
                        "+919999999999",
                        Json({"hotel_rating": "3-4", "meal": "non-veg"}),
                    ),
                )
            cur.execute("SELECT COUNT(*) AS count FROM tours")
            tours_count = cur.fetchone()[0]
            if tours_count == 0:
                cur.execute(
                    """
                    INSERT INTO tours (code, name, base_price, nights, destination)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        "GOA-5D4N-OPT2",
                        "Goa 5D/4N – Beachside",
                        38000,
                        4,
                        "Goa",
                    ),
                )
