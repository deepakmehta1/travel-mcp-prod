import hashlib
import os
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


def search_tours(
    destination: str | None = None, budget: int | None = None
) -> list[dict[str, Any]]:
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


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    iterations = 120000
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${dk.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iter_str, salt, digest = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return dk.hex() == digest
    except Exception:
        return False


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, phone, password_hash
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                """,
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "password_hash": row[4],
            }


def create_user(name: str, email: str, phone: str, password: str) -> dict[str, Any]:
    password_hash = _hash_password(password)
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, phone, password_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, email, phone
                """,
                (name, email, phone, password_hash),
            )
            row = cur.fetchone()
            # keep customers table aligned for booking flows
            cur.execute(
                """
                INSERT INTO customers (name, email, phone, preferences)
                VALUES (%s, %s, %s, '{}'::jsonb)
                ON CONFLICT (phone) DO NOTHING
                """,
                (name, email, phone),
            )
    return {"id": row[0], "name": row[1], "email": row[2], "phone": row[3]}


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_email(email)
    if not user:
        return None
    if not _verify_password(password, user["password_hash"]):
        return None
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
    }
