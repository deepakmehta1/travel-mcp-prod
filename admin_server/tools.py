import logging
from typing import Any, Dict

from fastmcp import FastMCP
from pydantic import ValidationError

from models import (
    BookingDetailModel,
    BookingStatsModel,
    CustomerDetailModel,
    GetBookingStatsRequest,
    GetBookingStatsResponse,
    GetRevenueReportRequest,
    GetRevenueReportResponse,
    ListAllBookingsRequest,
    ListAllBookingsResponse,
    ListAllCustomersRequest,
    ListAllCustomersResponse,
    ListAllToursRequest,
    ListAllToursResponse,
    RevenueReportModel,
    TourDetailModel,
    UpdateBookingStatusRequest,
    UpdateBookingStatusResponse,
)
from repositories import (
    get_all_bookings,
    get_all_customers,
    get_all_tours,
    get_booking_stats,
    get_revenue_report,
    update_booking_status,
)

logger = logging.getLogger("admin-server")


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def listAllBookings(
        status: str | None = None,
        destination: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List all bookings with optional filters.
        
        Args:
            status: Filter by booking status (confirmed, pending, cancelled)
            destination: Filter by destination
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)
        """
        try:
            req = ListAllBookingsRequest(
                status=status,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
            )
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return ListAllBookingsResponse(
                success=False, error="INVALID_REQUEST"
            ).model_dump()

        try:
            bookings, total = get_all_bookings(
                status=req.status,
                destination=req.destination,
                start_date=req.start_date,
                end_date=req.end_date,
                limit=req.limit,
                offset=req.offset,
            )
            return ListAllBookingsResponse(
                success=True,
                bookings=[BookingDetailModel(**b) for b in bookings],
                total=total,
            ).model_dump()
        except Exception as e:
            logger.exception("listAllBookings failed")
            return ListAllBookingsResponse(
                success=False, error=str(e)
            ).model_dump()

    @mcp.tool()
    def getBookingStats(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get booking statistics including total bookings, revenue, and breakdowns.
        
        Args:
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
        """
        try:
            req = GetBookingStatsRequest(start_date=start_date, end_date=end_date)
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return GetBookingStatsResponse(
                success=False, error="INVALID_REQUEST"
            ).model_dump()

        try:
            stats = get_booking_stats(
                start_date=req.start_date,
                end_date=req.end_date,
            )
            
            # Convert recent_bookings to BookingDetailModel
            recent_bookings = [
                BookingDetailModel(**b) for b in stats.pop("recent_bookings", [])
            ]
            
            return GetBookingStatsResponse(
                success=True,
                stats=BookingStatsModel(**stats, recent_bookings=recent_bookings),
            ).model_dump()
        except Exception as e:
            logger.exception("getBookingStats failed")
            return GetBookingStatsResponse(
                success=False, error=str(e)
            ).model_dump()

    @mcp.tool()
    def listAllCustomers(
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List all customers with their booking statistics.
        
        Args:
            search: Search by name, email, or phone
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)
        """
        try:
            req = ListAllCustomersRequest(
                search=search,
                limit=limit,
                offset=offset,
            )
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return ListAllCustomersResponse(
                success=False, error="INVALID_REQUEST"
            ).model_dump()

        try:
            customers, total = get_all_customers(
                search=req.search,
                limit=req.limit,
                offset=req.offset,
            )
            return ListAllCustomersResponse(
                success=True,
                customers=[CustomerDetailModel(**c) for c in customers],
                total=total,
            ).model_dump()
        except Exception as e:
            logger.exception("listAllCustomers failed")
            return ListAllCustomersResponse(
                success=False, error=str(e)
            ).model_dump()

    @mcp.tool()
    def listAllTours(destination: str | None = None) -> Dict[str, Any]:
        """
        List all tours with booking and revenue statistics.
        
        Args:
            destination: Filter by destination
        """
        try:
            req = ListAllToursRequest(destination=destination)
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return ListAllToursResponse(
                success=False, error="INVALID_REQUEST"
            ).model_dump()

        try:
            tours = get_all_tours(destination=req.destination)
            return ListAllToursResponse(
                success=True,
                tours=[TourDetailModel(**t) for t in tours],
            ).model_dump()
        except Exception as e:
            logger.exception("listAllTours failed")
            return ListAllToursResponse(
                success=False, error=str(e)
            ).model_dump()

    @mcp.tool()
    def updateBookingStatus(booking_id: int, status: str) -> Dict[str, Any]:
        """
        Update the status of a booking.
        
        Args:
            booking_id: The ID of the booking to update
            status: The new status (confirmed, pending, cancelled)
        """
        try:
            req = UpdateBookingStatusRequest(booking_id=booking_id, status=status)
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return UpdateBookingStatusResponse(
                success=False, error="INVALID_REQUEST"
            ).model_dump()

        try:
            success = update_booking_status(req.booking_id, req.status)
            if success:
                return UpdateBookingStatusResponse(
                    success=True,
                    message=f"Booking {req.booking_id} status updated to {req.status}",
                ).model_dump()
            else:
                return UpdateBookingStatusResponse(
                    success=False, error="UPDATE_FAILED"
                ).model_dump()
        except Exception as e:
            logger.exception("updateBookingStatus failed")
            return UpdateBookingStatusResponse(
                success=False, error=str(e)
            ).model_dump()

    @mcp.tool()
    def getRevenueReport(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get a comprehensive revenue report with breakdowns.
        
        Args:
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
        """
        try:
            req = GetRevenueReportRequest(start_date=start_date, end_date=end_date)
        except ValidationError as exc:
            logger.warning("Invalid request", extra={"errors": exc.errors()})
            return GetRevenueReportResponse(
                success=False, error="INVALID_REQUEST"
            ).model_dump()

        try:
            report = get_revenue_report(
                start_date=req.start_date,
                end_date=req.end_date,
            )
            return GetRevenueReportResponse(
                success=True,
                report=RevenueReportModel(**report),
            ).model_dump()
        except Exception as e:
            logger.exception("getRevenueReport failed")
            return GetRevenueReportResponse(
                success=False, error=str(e)
            ).model_dump()
