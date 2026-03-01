from datetime import date
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerModel(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    preferences: dict[str, Any] = Field(default_factory=dict)


class TourModel(BaseModel):
    code: str
    name: str
    base_price: int
    nights: int
    destination: str


class TourSummaryModel(BaseModel):
    code: str
    name: str
    price: int
    nights: int
    destination: str


class BookingModel(BaseModel):
    id: int
    customer_id: int
    tour_code: str
    start_date: date
    end_date: date
    total_price: int
    status: str


class LookupCustomerByPhoneRequest(BaseModel):
    phone: str = Field(min_length=3)


class LookupCustomerByPhoneResponse(BaseModel):
    found: bool
    customer: CustomerModel | None = None
    error: str | None = None


class SearchToursRequest(BaseModel):
    destination: str | None = None
    budget: int | None = Field(default=None, ge=0)


class SearchToursResponse(BaseModel):
    tours: list[TourSummaryModel]
    error: str | None = None


class BookTourRequest(BaseModel):
    customer_id: int = Field(ge=1)
    tour_code: str = Field(min_length=3)
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, value: date, info):
        start_date = info.data.get("start_date")
        if start_date and value < start_date:
            raise ValueError("end_date must be on or after start_date")
        return value


class BookTourResponse(BaseModel):
    success: bool
    booking: BookingModel | None = None
    error: str | None = None


class RegisterUserRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    phone: str = Field(min_length=3)
    password: str = Field(min_length=6)


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class AuthUserModel(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str


class RegisterUserResponse(BaseModel):
    success: bool
    user: AuthUserModel | None = None
    error: str | None = None


class LoginUserResponse(BaseModel):
    success: bool
    user: AuthUserModel | None = None
    error: str | None = None
