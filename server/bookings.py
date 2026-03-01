from typing import Any

try:
    from .db import get_pool
except ImportError:
    from db import get_pool


def list_bookings_by_phone(phone: str) -> list[dict[str, Any]]:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT b.id, b.customer_id, b.tour_code, b.start_date, b.end_date,
                       b.total_price, b.status, t.name, t.destination, t.nights
                FROM bookings b
                JOIN customers c ON c.id = b.customer_id
                JOIN tours t ON t.code = b.tour_code
                WHERE c.phone = %s
                ORDER BY b.created_at DESC
                """,
                (phone,),
            )
            rows = cur.fetchall()

    results = []
    for row in rows:
        results.append(
            {
                "id": row[0],
                "customer_id": row[1],
                "tour_code": row[2],
                "start_date": (
                    row[3].isoformat() if hasattr(row[3], "isoformat") else row[3]
                ),
                "end_date": (
                    row[4].isoformat() if hasattr(row[4], "isoformat") else row[4]
                ),
                "total_price": row[5],
                "status": row[6],
                "tour_name": row[7],
                "destination": row[8],
                "nights": row[9],
            }
        )
    return results
