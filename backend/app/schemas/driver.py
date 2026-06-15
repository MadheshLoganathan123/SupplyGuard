"""
Pydantic schemas for Driver — request / response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


VEHICLE_TYPES = ("motorcycle", "cargo_bike", "van", "truck", "drone", "aerial")
DRIVER_STATUSES = ("idle", "active", "en_route", "offline")


class DriverBase(BaseModel):
    vehicle_type: str = Field("motorcycle", examples=["cargo_bike"])
    vehicle_plate: Optional[str] = Field(None, max_length=20, examples=["KHI-4821"])
    capacity_kg: Optional[Decimal] = Field(None, ge=0, examples=[200.0])
    sector: Optional[str] = Field(None, max_length=50, examples=["Sector 7"])
    status: str = Field("idle", examples=["active"])
    current_lat: Optional[Decimal] = Field(None, examples=[24.8607])
    current_lng: Optional[Decimal] = Field(None, examples=[67.0011])
    utilization_pct: Decimal = Field(Decimal("0.0"), ge=0, le=100, examples=[78.5])
    agent_code: Optional[str] = Field(None, max_length=100, examples=["Logi-Truck-9"])

    @field_validator("vehicle_type")
    @classmethod
    def validate_vehicle_type(cls, v: str) -> str:
        if v not in VEHICLE_TYPES:
            raise ValueError(f"vehicle_type must be one of: {', '.join(VEHICLE_TYPES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in DRIVER_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(DRIVER_STATUSES)}")
        return v


class DriverCreate(DriverBase):
    """Body for POST /drivers"""
    user_id: Optional[str] = Field(None, description="UUID of the linked platform user")


class DriverUpdate(BaseModel):
    """Body for PATCH /drivers/{id}"""
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = Field(None, max_length=20)
    capacity_kg: Optional[Decimal] = Field(None, ge=0)
    sector: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    current_lat: Optional[Decimal] = None
    current_lng: Optional[Decimal] = None
    utilization_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    agent_code: Optional[str] = Field(None, max_length=100)

    @field_validator("vehicle_type")
    @classmethod
    def validate_vehicle_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VEHICLE_TYPES:
            raise ValueError(f"vehicle_type must be one of: {', '.join(VEHICLE_TYPES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in DRIVER_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(DRIVER_STATUSES)}")
        return v


class DriverRead(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DriverListResponse(BaseModel):
    total: int
    items: list[DriverRead]
