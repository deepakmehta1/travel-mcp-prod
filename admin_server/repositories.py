import logging
from datetime import date
from typing import Any

from db import execute_query

logger = logging.getLogger("admin-server")


def get_all_bookings(
    status: str | None = None,
    destination: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Get all bookings with optional filters"""
    
    # Build the WHERE clause dynamically
    where_clauses = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    
    if status:
        where_clauses.append("b.status = :status")
        params["status"] = status
    
    if destination:
        where_clauses.append("t.destination ILIKE :destination")
        params["destination"] = f"%{destination}%"
    
    if start_date:
        where_clauses.append("b.start_date >= :start_date")
        params["start_date"] = start_date
    
    if end_date:
        where_clauses.append("b.end_date <= :end_date")
        params["end_date"] = end_date
    
    where_clause = " AND " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN tours t ON b.tour_code = t.code
        WHERE 1=1{where_clause}
    """
    count_result = execute_query(count_query, params)
    total = count_result[0]["total"] if count_result else 0
    
    # Get bookings
    query = f"""
        SELECT 
            b.id,
            b.customer_id,
            c.name as customer_name,
            c.email as customer_email,
            c.phone as customer_phone,
            b.tour_code,
            t.name as tour_name,
            t.destination,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status,
            b.created_at
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN tours t ON b.tour_code = t.code
        WHERE 1=1{where_clause}
        ORDER BY b.created_at DESC
        LIMIT :limit OFFSET :offset
    """
    
    bookings = execute_query(query, params)
    return bookings, total


def get_booking_stats(
    start_date: date | None = None,
    end_date: date | None = None
) -> dict[str, Any]:
    """Get booking statistics"""
    
    where_clauses = []
    params: dict[str, Any] = {}
    
    if start_date:
        where_clauses.append("b.start_date >= :start_date")
        params["start_date"] = start_date
    
    if end_date:
        where_clauses.append("b.end_date <= :end_date")
        params["end_date"] = end_date
    
    where_clause = " AND " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Get overall stats
    stats_query = f"""
        SELECT 
            COUNT(*) as total_bookings,
            COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_bookings,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_bookings,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_bookings,
            COALESCE(SUM(CASE WHEN status = 'confirmed' THEN total_price ELSE 0 END), 0) as total_revenue
        FROM bookings b
        WHERE 1=1{where_clause}
    """
    stats_result = execute_query(stats_query, params)
    stats = stats_result[0] if stats_result else {}
    
    # Get bookings by destination
    dest_query = f"""
        SELECT t.destination, COUNT(*) as count
        FROM bookings b
        JOIN tours t ON b.tour_code = t.code
        WHERE 1=1{where_clause}
        GROUP BY t.destination
        ORDER BY count DESC
    """
    dest_result = execute_query(dest_query, params)
    bookings_by_destination = {row["destination"]: row["count"] for row in dest_result}
    
    # Get recent bookings
    recent_query = f"""
        SELECT 
            b.id,
            b.customer_id,
            c.name as customer_name,
            c.email as customer_email,
            c.phone as customer_phone,
            b.tour_code,
            t.name as tour_name,
            t.destination,
            b.start_date,
            b.end_date,
            b.total_price,
            b.status,
            b.created_at
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN tours t ON b.tour_code = t.code
        WHERE 1=1{where_clause}
        ORDER BY b.created_at DESC
        LIMIT 10
    """
    recent_bookings = execute_query(recent_query, params)
    
    return {
        **stats,
        "bookings_by_destination": bookings_by_destination,
        "recent_bookings": recent_bookings
    }


def get_all_customers(
    search: str | None = None,
    limit: int = 100,
    offset: int = 0
) -> tuple[list[dict[str, Any]], int]:
    """Get all customers with optional search"""
    
    where_clause = ""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    
    if search:
        where_clause = " AND (c.name ILIKE :search OR c.email ILIKE :search OR c.phone ILIKE :search)"
        params["search"] = f"%{search}%"
    
    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM customers c
        WHERE 1=1{where_clause}
    """
    count_result = execute_query(count_query, params)
    total = count_result[0]["total"] if count_result else 0
    
    # Get customers with booking stats
    query = f"""
        SELECT 
            c.id,
            c.name,
            c.email,
            c.phone,
            c.preferences,
            COUNT(b.id) as total_bookings,
            COALESCE(SUM(CASE WHEN b.status = 'confirmed' THEN b.total_price ELSE 0 END), 0) as total_spent
        FROM customers c
        LEFT JOIN bookings b ON c.id = b.customer_id
        WHERE 1=1{where_clause}
        GROUP BY c.id, c.name, c.email, c.phone, c.preferences
        ORDER BY total_spent DESC
        LIMIT :limit OFFSET :offset
    """
    
    customers = execute_query(query, params)
    return customers, total


def get_all_tours(destination: str | None = None) -> list[dict[str, Any]]:
    """Get all tours with booking stats"""
    
    where_clause = ""
    params: dict[str, Any] = {}
    
    if destination:
        where_clause = " WHERE t.destination ILIKE :destination"
        params["destination"] = f"%{destination}%"
    
    query = f"""
        SELECT 
            t.code,
            t.name,
            t.base_price,
            t.nights,
            t.destination,
            COUNT(b.id) as total_bookings,
            COALESCE(SUM(CASE WHEN b.status = 'confirmed' THEN b.total_price ELSE 0 END), 0) as revenue
        FROM tours t
        LEFT JOIN bookings b ON t.code = b.tour_code
        {where_clause}
        GROUP BY t.code, t.name, t.base_price, t.nights, t.destination
        ORDER BY revenue DESC
    """
    
    return execute_query(query, params)


def update_booking_status(booking_id: int, status: str) -> bool:
    """Update booking status"""
    
    query = """
        UPDATE bookings
        SET status = :status
        WHERE id = :booking_id
    """
    
    try:
        execute_query(query, {"booking_id": booking_id, "status": status})
        return True
    except Exception as e:
        logger.error(f"Failed to update booking status: {e}")
        return False


def get_revenue_report(
    start_date: date | None = None,
    end_date: date | None = None
) -> dict[str, Any]:
    """Get revenue report"""
    
    where_clauses = ["b.status = 'confirmed'"]
    params: dict[str, Any] = {}
    
    if start_date:
        where_clauses.append("b.start_date >= :start_date")
        params["start_date"] = start_date
    
    if end_date:
        where_clauses.append("b.end_date <= :end_date")
        params["end_date"] = end_date
    
    where_clause = " AND " + " AND ".join(where_clauses) if len(where_clauses) > 1 else f" AND {where_clauses[0]}"
    
    # Total revenue
    revenue_query = f"""
        SELECT COALESCE(SUM(total_price), 0) as total_revenue
        FROM bookings b
        WHERE 1=1{where_clause}
    """
    revenue_result = execute_query(revenue_query, params)
    total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
    
    # Revenue by destination
    dest_query = f"""
        SELECT t.destination, COALESCE(SUM(b.total_price), 0) as revenue
        FROM bookings b
        JOIN tours t ON b.tour_code = t.code
        WHERE 1=1{where_clause}
        GROUP BY t.destination
        ORDER BY revenue DESC
    """
    dest_result = execute_query(dest_query, params)
    revenue_by_destination = {row["destination"]: row["revenue"] for row in dest_result}
    
    # Revenue by month
    month_query = f"""
        SELECT 
            TO_CHAR(b.start_date, 'YYYY-MM') as month,
            COALESCE(SUM(b.total_price), 0) as revenue
        FROM bookings b
        WHERE 1=1{where_clause}
        GROUP BY TO_CHAR(b.start_date, 'YYYY-MM')
        ORDER BY month DESC
    """
    month_result = execute_query(month_query, params)
    revenue_by_month = {row["month"]: row["revenue"] for row in month_result}
    
    # Top tours
    top_tours_query = f"""
        SELECT 
            t.code,
            t.name,
            t.destination,
            COUNT(b.id) as bookings,
            COALESCE(SUM(b.total_price), 0) as revenue
        FROM bookings b
        JOIN tours t ON b.tour_code = t.code
        WHERE 1=1{where_clause}
        GROUP BY t.code, t.name, t.destination
        ORDER BY revenue DESC
        LIMIT 10
    """
    top_tours = execute_query(top_tours_query, params)
    
    return {
        "total_revenue": total_revenue,
        "revenue_by_destination": revenue_by_destination,
        "revenue_by_month": revenue_by_month,
        "top_tours": top_tours
    }
