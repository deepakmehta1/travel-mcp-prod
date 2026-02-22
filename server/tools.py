import logging
from datetime import date
from typing import Any, Dict

from fastmcp import FastMCP
from pydantic import ValidationError

from .models import (
    BookTourRequest,
    BookTourResponse,
    LookupCustomerByPhoneRequest,
    LookupCustomerByPhoneResponse,
    SearchToursRequest,
    SearchToursResponse,
)
from .repositories import (
    create_booking,
    get_customer_by_id,
    get_customer_by_phone,
    get_tour_by_code,
    search_tours,
)

logger = logging.getLogger("server")


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def lookupCustomerByPhone(phone: str) -> Dict[str, Any]:
        try:
            req = LookupCustomerByPhoneRequest(phone=phone)
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return {"found": False, "error": "INVALID_REQUEST"}

        logger.info("lookupCustomerByPhone called", extra={"phone": req.phone})
        customer = get_customer_by_phone(phone)
        if not customer:
            logger.info("Customer not found", extra={"phone": phone})
            return LookupCustomerByPhoneResponse(found=False).model_dump()
        logger.info("Customer found", extra={"customer_id": customer["id"]})
        response = LookupCustomerByPhoneResponse(found=True, customer=customer)
        return response.model_dump()

    @mcp.tool()
    def searchTours(destination: str | None = None, budget: int | None = None) -> Dict[str, Any]:
        try:
            req = SearchToursRequest(destination=destination, budget=budget)
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return {"tours": [], "error": "INVALID_REQUEST"}

        logger.info(
            "searchTours called",
            extra={"destination": req.destination, "budget": req.budget},
        )
        results = search_tours(destination=req.destination, budget=req.budget)
        response = [
            {
                "code": t["code"],
                "name": t["name"],
                "price": t["base_price"],
                "nights": t["nights"],
                "destination": t["destination"],
            }
            for t in results
        ]
        logger.info("searchTours returning results", extra={"count": len(response)})
        return SearchToursResponse(tours=response).model_dump()

    @mcp.tool()
    def bookTour(
        customer_id: int,
        tour_code: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        try:
            req = BookTourRequest(
                customer_id=customer_id,
                tour_code=tour_code,
                start_date=date.fromisoformat(start_date),
                end_date=date.fromisoformat(end_date),
            )
        except ValueError:
            logger.warning(
                "Invalid date format",
                extra={"start_date": start_date, "end_date": end_date},
            )
            return BookTourResponse(success=False, error="INVALID_DATE_FORMAT").model_dump()
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return BookTourResponse(success=False, error="INVALID_REQUEST").model_dump()

        logger.info(
            "bookTour called",
            extra={
                "customer_id": req.customer_id,
                "tour_code": req.tour_code,
                "start_date": req.start_date.isoformat(),
                "end_date": req.end_date.isoformat(),
            },
        )

        customer = get_customer_by_id(req.customer_id)
        if not customer:
            logger.warning("Customer not found", extra={"customer_id": req.customer_id})
            return BookTourResponse(success=False, error="CUSTOMER_NOT_FOUND").model_dump()

        tour = get_tour_by_code(req.tour_code)
        if not tour:
            logger.warning("Tour not found", extra={"tour_code": req.tour_code})
            return BookTourResponse(success=False, error="TOUR_NOT_FOUND").model_dump()

        booking = create_booking(
            customer_id=req.customer_id,
            tour_code=req.tour_code,
            start_date=req.start_date,
            end_date=req.end_date,
            total_price=tour["base_price"],
            status="CONFIRMED",
        )

        logger.info("Booking created", extra={"booking_id": booking["id"]})
        return BookTourResponse(success=True, booking=booking).model_dump()
