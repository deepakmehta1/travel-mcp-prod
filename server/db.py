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

SEED_TOURS = [
    ("GOA-5D4N-OPT2", "Goa 5D/4N – Beachside", 38000, 4, "Goa"),
    ("DEL-3D2N-CITY", "Delhi 3D/2N – Heritage", 22000, 2, "Delhi"),
    ("BLR-3D2N-URBAN", "Bengaluru 3D/2N – Tech & Food", 21000, 2, "Bengaluru"),
    ("MUM-4D3N-COAST", "Mumbai 4D/3N – City & Coast", 26000, 3, "Mumbai"),
    ("JAIP-4D3N-PINK", "Jaipur 4D/3N – Forts & Bazaars", 24000, 3, "Jaipur"),
    ("KER-5D4N-BACK", "Kerala 5D/4N – Backwaters", 42000, 4, "Kerala"),
    ("LAD-6D5N-ALT", "Ladakh 6D/5N – High Altitude", 52000, 5, "Ladakh"),
    ("AGN-3D2N-WINE", "Nashik 3D/2N – Vineyards", 18000, 2, "Nashik"),
    ("KOL-3D2N-ART", "Kolkata 3D/2N – Culture & Cuisine", 20000, 2, "Kolkata"),
    ("PUN-3D2N-FOOD", "Pune 3D/2N – Food & History", 19000, 2, "Pune"),
    ("HYD-4D3N-CHAR", "Hyderabad 4D/3N – Charminar & Biryani", 23000, 3, "Hyderabad"),
]


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
            extra={
                "min_size": settings.pool_min_size,
                "max_size": settings.pool_max_size,
            },
        )
    return _pool


def init_db() -> None:
    schema_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
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
            if tours_count < len(SEED_TOURS):
                cur.executemany(
                    """
                    INSERT INTO tours (code, name, base_price, nights, destination)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (code) DO NOTHING
                    """,
                    SEED_TOURS,
                )
