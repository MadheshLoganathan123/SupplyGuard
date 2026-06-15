"""
Pydantic schemas for Inventory — request / response validation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


CATEGORIES = ("grain", "produce", "dairy", "protein", "medical", "water", "general")
UNITS = ("kg", "litre", "units", "tonnes", "boxes")


class InventoryBase(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=255, examples=["Wheat Flour"])
    category: str = Field("general", examples=["grain"])
    quantity: Decimal = Field(..., ge=0, examples=[500.0])
    unit: str = Field("kg", examples=["kg"])
    min_threshold: Decimal = Field(Decimal("0"), ge=0, examples=[50.0])
    max_capacity: Optional[Decimal] = Field(None, ge=0, examples=[2000.0])
    expiry_date: Optional[date] = Field(None, examples=["2025-12-31"])

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(CATEGORIES)}")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        if v not in UNITS:
            raise ValueError(f"unit must be one of: {', '.join(UNITS)}")
        return v


class InventoryCreate(InventoryBase):
    """
    Body for POST /inventory.
    Exactly one of farmer_id, store_id, or pantry_id must be provided.
    """
    farmer_id: Optional[str] = Field(None, description="Owner farmer UUID")
    store_id: Optional[str] = Field(None, description="Owner store UUID")
    pantry_id: Optional[str] = Field(None, description="Owner pantry UUID")
    last_updated_by: Optional[str] = Field(None, description="User UUID who updated stock")

    @model_validator(mode="after")
    def validate_single_owner(self) -> "InventoryCreate":
        owners = [
            self.farmer_id,
            self.store_id,
            self.pantry_id,
        ]
        filled = sum(1 for o in owners if o is not None)
        if filled != 1:
            raise ValueError(
                "Exactly one of farmer_id, store_id, or pantry_id must be provided."
            )
        return self


class InventoryUpdate(BaseModel):
    """Body for PATCH /inventory/{id} — all optional"""
    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit: Optional[str] = None
    min_threshold: Optional[Decimal] = Field(None, ge=0)
    max_capacity: Optional[Decimal] = Field(None, ge=0)
    expiry_date: Optional[date] = None
    last_updated_by: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(CATEGORIES)}")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in UNITS:
            raise ValueError(f"unit must be one of: {', '.join(UNITS)}")
        return v


class InventoryRead(InventoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    farmer_id: Optional[str] = None
    store_id: Optional[str] = None
    pantry_id: Optional[str] = None
    last_updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Derived helper
    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.min_threshold


class InventoryListResponse(BaseModel):
    total: int
    items: list[InventoryRead]
