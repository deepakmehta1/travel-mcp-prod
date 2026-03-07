from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class BookingDetailModel(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    customer_phone: str
    tour_code: str
    tour_name: str
    destination: str
    start_date: date
    end_date: date
    total_price: int
    status: str
    created_at: datetime | None = None


class ListAllBookingsRequest(BaseModel):
    status: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ListAllBookingsResponse(BaseModel):
    success: bool
    bookings: list[BookingDetailModel] | None = None
    total: int = 0
    error: str | None = None


class BookingStatsModel(BaseModel):
    total_bookings: int
    confirmed_bookings: int
    pending_bookings: int
    cancelled_bookings: int
    total_revenue: int
    bookings_by_destination: dict[str, int]
    recent_bookings: list[BookingDetailModel]


class GetBookingStatsRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class GetBookingStatsResponse(BaseModel):
    success: bool
    stats: BookingStatsModel | None = None
    error: str | None = None


class CustomerDetailModel(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    total_bookings: int
    total_spent: int
    preferences: dict[str, Any] = Field(default_factory=dict)


class ListAllCustomersRequest(BaseModel):
    search: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ListAllCustomersResponse(BaseModel):
    success: bool
    customers: list[CustomerDetailModel] | None = None
    total: int = 0
    error: str | None = None


class TourDetailModel(BaseModel):
    code: str
    name: str
    base_price: int
    nights: int
    destination: str
    total_bookings: int
    revenue: int


class ListAllToursRequest(BaseModel):
    destination: str | None = None


class ListAllToursResponse(BaseModel):
    success: bool
    tours: list[TourDetailModel] | None = None
    error: str | None = None


class UpdateBookingStatusRequest(BaseModel):
    booking_id: int = Field(ge=1)
    status: str = Field(min_length=2)


class UpdateBookingStatusResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None


class RevenueReportModel(BaseModel):
    total_revenue: int
    revenue_by_destination: dict[str, int]
    revenue_by_month: dict[str, int]
    top_tours: list[dict[str, Any]]


class GetRevenueReportRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class GetRevenueReportResponse(BaseModel):
    success: bool
    report: RevenueReportModel | None = None
    error: str | None = None
