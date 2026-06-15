"""
Pydantic schemas for Farmer — request / response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


FARM_TYPES = ("conventional", "vertical", "greenhouse", "hydroponic", "organic")


class FarmerBase(BaseModel):
    farm_name: str = Field(..., min_length=2, max_length=255, examples=["Green Valley Farm"])
    farm_type: str = Field("conventional", examples=["vertical"])
    sector: Optional[str] = Field(None, max_length=50, examples=["Sector 7"])
    latitude: Optional[Decimal] = Field(None, examples=[24.8607])
    longitude: Optional[Decimal] = Field(None, examples=[67.0011])
    total_area_sqm: Optional[Decimal] = Field(None, ge=0, examples=[5000.0])
    agent_code: Optional[str] = Field(None, max_length=100, examples=["Alpha-9"])

    @field_validator("farm_type")
    @classmethod
    def validate_farm_type(cls, v: str) -> str:
        if v not in FARM_TYPES:
            raise ValueError(f"farm_type must be one of: {', '.join(FARM_TYPES)}")
        return v


class FarmerCreate(FarmerBase):
    """Body for POST /farmers"""
    user_id: Optional[str] = Field(None, description="UUID of the linked platform user")


class FarmerUpdate(BaseModel):
    """Body for PATCH /farmers/{id} — all fields optional"""
    farm_name: Optional[str] = Field(None, min_length=2, max_length=255)
    farm_type: Optional[str] = None
    sector: Optional[str] = Field(None, max_length=50)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    total_area_sqm: Optional[Decimal] = Field(None, ge=0)
    agent_code: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

    @field_validator("farm_type")
    @classmethod
    def validate_farm_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in FARM_TYPES:
            raise ValueError(f"farm_type must be one of: {', '.join(FARM_TYPES)}")
        return v


class FarmerRead(FarmerBase):
    """Response schema — includes DB-generated fields"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FarmerListResponse(BaseModel):
    """Paginated list wrapper"""
    total: int
    items: list[FarmerRead]
