import logging
import logging.config
import os
from datetime import date
from typing import Dict, Any, List

from fastmcp import FastMCP  # part of mcp[fm][web:61][web:87]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(BASE_DIR, "logging.conf")

if os.path.exists(LOGGING_CONF):
    logging.config.fileConfig(LOGGING_CONF)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("server")

mcp = FastMCP(name="Travel Demo MCP Server")

# In-memory data (swap with Postgres later)
CUSTOMERS = {
    "+919999999999": {
        "id": 1,
        "name": "Deepak Mehta",
        "email": "deepak@example.com",
        "phone": "+919999999999",
        "preferences": {"hotel_rating": "3-4", "meal": "non-veg"},
    }
}

TOURS = [
    {
        "code": "GOA-5D4N-OPT2",
        "name": "Goa 5D/4N – Beachside",
        "base_price": 38000,
        "nights": 4,
        "destination": "Goa",
    },
]

BOOKINGS: List[Dict[str, Any]] = []
BOOKING_ID_COUNTER = 1


@mcp.tool()
def lookupCustomerByPhone(phone: str) -> Dict[str, Any]:
    logger.info("lookupCustomerByPhone called", extra={"phone": phone})
    customer = CUSTOMERS.get(phone)
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
    results = []
    for t in TOURS:
        if destination and t["destination"].lower() != destination.lower():
            continue
        if budget is not None and t["base_price"] > budget:
            continue
        results.append(
            {
                "code": t["code"],
                "name": t["name"],
                "price": t["base_price"],
                "nights": t["nights"],
                "destination": t["destination"],
            }
        )
    logger.info("searchTours returning results", extra={"count": len(results)})
    return {"tours": results}


@mcp.tool()
def bookTour(
    customer_id: int,
    tour_code: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    global BOOKING_ID_COUNTER

    logger.info(
        "bookTour called",
        extra={
            "customer_id": customer_id,
            "tour_code": tour_code,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    tour = next((t for t in TOURS if t["code"] == tour_code), None)
    if not tour:
        logger.warning("Tour not found", extra={"tour_code": tour_code})
        return {"success": False, "error": "TOUR_NOT_FOUND"}

    try:
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)
    except ValueError:
        logger.warning("Invalid date format", extra={"start_date": start_date, "end_date": end_date})
        return {"success": False, "error": "INVALID_DATE_FORMAT"}

    total_price = tour["base_price"]

    booking = {
        "id": BOOKING_ID_COUNTER,
        "customer_id": customer_id,
        "tour_code": tour_code,
        "start_date": sd.isoformat(),
        "end_date": ed.isoformat(),
        "total_price": total_price,
        "status": "CONFIRMED",
    }
    BOOKINGS.append(booking)
    BOOKING_ID_COUNTER += 1

    logger.info("Booking created", extra={"booking_id": booking["id"]})
    return {"success": True, "booking": booking}


if __name__ == "__main__":
    logger.info("Starting Travel MCP Server (stdio)")
    mcp.run(transport="stdio")
