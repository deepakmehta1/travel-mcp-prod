import logging
import logging.config
import os
from datetime import date
from typing import Dict, Any, List

from fastmcp import FastMCP  # part of mcp[fm][web:61][web:87]
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(BASE_DIR, "logging.conf")

if os.path.exists(LOGGING_CONF):
    logging.config.fileConfig(LOGGING_CONF)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("server")

mcp = FastMCP(name="Travel Demo MCP Server")

DEFAULT_DB_HOST = os.getenv("PGHOST", "localhost")
DEFAULT_DB_PORT = os.getenv("PGPORT", "5432")
DEFAULT_DB_NAME = os.getenv("PGDATABASE", "travel")
DEFAULT_DB_USER = os.getenv("PGUSER", "postgres")
DEFAULT_DB_PASSWORD = os.getenv("PGPASSWORD", "postgres")


def _db_conninfo() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return (
        f"postgresql://{DEFAULT_DB_USER}:{DEFAULT_DB_PASSWORD}"
        f"@{DEFAULT_DB_HOST}:{DEFAULT_DB_PORT}/{DEFAULT_DB_NAME}"
    )


def _get_conn() -> psycopg.Connection:
    return psycopg.connect(_db_conninfo(), row_factory=dict_row)


def _init_db() -> None:
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
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            cur.execute("SELECT COUNT(*) AS count FROM customers")
            customers_count = cur.fetchone()["count"]
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
            tours_count = cur.fetchone()["count"]
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


_init_db()


@mcp.tool()
def lookupCustomerByPhone(phone: str) -> Dict[str, Any]:
    logger.info("lookupCustomerByPhone called", extra={"phone": phone})
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, phone, preferences
                FROM customers
                WHERE phone = %s
                """,
                (phone,),
            )
            customer = cur.fetchone()
    if not customer:
        logger.info("Customer not found", extra={"phone": phone})
        return {"found": False}
    logger.info("Customer found", extra={"customer_id": customer["id"]})
    return {"found": True, "customer": customer}


@mcp.tool()
def searchTours(destination: str | None = None, budget: int | None = None) -> Dict[str, Any]:
    logger.info(
        "searchTours called",
        extra={"destination": destination, "budget": budget},
    )
    filters = []
    params: list[Any] = []
    if destination:
        filters.append("LOWER(destination) = LOWER(%s)")
        params.append(destination)
    if budget is not None:
        filters.append("base_price <= %s")
        params.append(budget)
    where_clause = " AND ".join(filters)
    sql = """
        SELECT code, name, base_price, nights, destination
        FROM tours
    """
    if where_clause:
        sql += f" WHERE {where_clause}"

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

    results = [
        {
            "code": r["code"],
            "name": r["name"],
            "price": r["base_price"],
            "nights": r["nights"],
            "destination": r["destination"],
        }
        for r in rows
    ]
    logger.info("searchTours returning results", extra={"count": len(results)})
    return {"tours": results}


@mcp.tool()
def bookTour(
    customer_id: int,
    tour_code: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    logger.info(
        "bookTour called",
        extra={
            "customer_id": customer_id,
            "tour_code": tour_code,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    try:
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)
    except ValueError:
        logger.warning("Invalid date format", extra={"start_date": start_date, "end_date": end_date})
        return {"success": False, "error": "INVALID_DATE_FORMAT"}

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM customers WHERE id = %s", (customer_id,))
            if not cur.fetchone():
                logger.warning("Customer not found", extra={"customer_id": customer_id})
                return {"success": False, "error": "CUSTOMER_NOT_FOUND"}

            cur.execute(
                "SELECT code, base_price FROM tours WHERE code = %s",
                (tour_code,),
            )
            tour = cur.fetchone()
            if not tour:
                logger.warning("Tour not found", extra={"tour_code": tour_code})
                return {"success": False, "error": "TOUR_NOT_FOUND"}

            total_price = tour["base_price"]
            cur.execute(
                """
                INSERT INTO bookings (
                    customer_id, tour_code, start_date, end_date, total_price, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, customer_id, tour_code, start_date, end_date, total_price, status
                """,
                (
                    customer_id,
                    tour_code,
                    sd,
                    ed,
                    total_price,
                    "CONFIRMED",
                ),
            )
            booking = cur.fetchone()

    logger.info("Booking created", extra={"booking_id": booking["id"]})
    return {"success": True, "booking": booking}


if __name__ == "__main__":
    logger.info("Starting Travel MCP Server (stdio)")
    mcp.run(transport="stdio")
