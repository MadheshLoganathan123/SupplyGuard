"""
Pydantic schemas for Store — request / response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


STORE_TYPES = ("retail", "wholesale", "cooperative", "emergency_hub")


class StoreBase(BaseModel):
    store_name: str = Field(..., min_length=2, max_length=255, examples=["Central Wholesale Hub"])
    store_type: str = Field("retail", examples=["wholesale"])
    sector: Optional[str] = Field(None, max_length=50, examples=["Sector 12"])
    address: Optional[str] = Field(None, examples=["Block 4, Main Market Road"])
    latitude: Optional[Decimal] = Field(None, examples=[24.8607])
    longitude: Optional[Decimal] = Field(None, examples=[67.0011])

    @field_validator("store_type")
    @classmethod
    def validate_store_type(cls, v: str) -> str:
        if v not in STORE_TYPES:
            raise ValueError(f"store_type must be one of: {', '.join(STORE_TYPES)}")
        return v


class StoreCreate(StoreBase):
    """Body for POST /stores"""
    manager_id: Optional[str] = Field(None, description="UUID of the store manager user")


class StoreUpdate(BaseModel):
    """Body for PATCH /stores/{id}"""
    store_name: Optional[str] = Field(None, min_length=2, max_length=255)
    store_type: Optional[str] = None
    sector: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_active: Optional[bool] = None
    manager_id: Optional[str] = None

    @field_validator("store_type")
    @classmethod
    def validate_store_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in STORE_TYPES:
            raise ValueError(f"store_type must be one of: {', '.join(STORE_TYPES)}")
        return v


class StoreRead(StoreBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    manager_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StoreListResponse(BaseModel):
    total: int
    items: list[StoreRead]
