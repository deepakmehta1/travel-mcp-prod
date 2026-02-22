from typing import Any

try:
    from .db import get_pool
except ImportError:
    from db import get_pool


def get_customer_by_phone(phone: str) -> dict[str, Any] | None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, phone, preferences
                FROM customers
                WHERE phone = %s
                """,
                (phone,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "preferences": row[4],
            }


def get_customer_by_id(customer_id: int) -> dict[str, Any] | None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, phone, preferences
                FROM customers
                WHERE id = %s
                """,
                (customer_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "preferences": row[4],
            }


def get_tour_by_code(tour_code: str) -> dict[str, Any] | None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT code, name, base_price, nights, destination
                FROM tours
                WHERE code = %s
                """,
                (tour_code,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "code": row[0],
                "name": row[1],
                "base_price": row[2],
                "nights": row[3],
                "destination": row[4],
            }


def search_tours(destination: str | None = None, budget: int | None = None) -> list[dict[str, Any]]:
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

    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

    return [
        {
            "code": row[0],
            "name": row[1],
            "base_price": row[2],
            "nights": row[3],
            "destination": row[4],
        }
        for row in rows
    ]


def create_booking(
    customer_id: int,
    tour_code: str,
    start_date: str,
    end_date: str,
    total_price: int,
    status: str,
) -> dict[str, Any]:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
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
                    start_date,
                    end_date,
                    total_price,
                    status,
                ),
            )
            row = cur.fetchone()

    return {
        "id": row[0],
        "customer_id": row[1],
        "tour_code": row[2],
        "start_date": row[3].isoformat() if hasattr(row[3], "isoformat") else row[3],
        "end_date": row[4].isoformat() if hasattr(row[4], "isoformat") else row[4],
        "total_price": row[5],
        "status": row[6],
    }
