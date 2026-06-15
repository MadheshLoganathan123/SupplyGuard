"""
Profiles endpoints — manage user profiles across all roles.

Routes:
- GET /api/profiles/me — fetch current user's full profile
- GET /api/profiles/{user_id} — admin: fetch any user's profile
- POST /api/profiles/update-base — update base profile fields
- POST /api/profiles/{role}/update — update role-specific profile
- GET /api/profiles/discover?role=...&... — discover users by criteria
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


# ─────────────────────────────────────────────────────────────────────────────
# Schema definitions
# ─────────────────────────────────────────────────────────────────────────────

class BaseProfileUpdate(BaseModel):
    """Update base profile fields."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability_status: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None


class FarmerProfileUpdate(BaseModel):
    """Update farmer-specific profile fields."""
    farm_name: Optional[str] = None
    farm_type: Optional[str] = None
    crops_produced: Optional[List[str]] = None
    farm_size_acres: Optional[float] = None
    available_quantity: Optional[float] = None
    expected_harvest_date: Optional[str] = None
    storage_availability: Optional[str] = None
    can_self_deliver: Optional[bool] = None
    max_delivery_distance_km: Optional[float] = None
    organic_certification: Optional[str] = None
    government_registration_number: Optional[str] = None
    fssai_number: Optional[str] = None


class DriverProfileUpdate(BaseModel):
    """Update driver-specific profile fields."""
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    max_load_kg: Optional[float] = None
    vehicle_capacity_description: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[str] = None
    vehicle_insurance_provider: Optional[str] = None
    insurance_valid_until: Optional[str] = None
    permit_reference: Optional[str] = None
    operating_radius_km: Optional[float] = None
    available_weekdays: Optional[str] = None
    night_delivery_allowed: Optional[bool] = None
    flood_zone_access: Optional[bool] = None
    emergency_ready: Optional[bool] = None


class StoreProfileUpdate(BaseModel):
    """Update store owner-specific profile fields."""
    store_name: Optional[str] = None
    store_type: Optional[str] = None
    inventory_categories: Optional[List[str]] = None
    cold_storage_capacity: Optional[float] = None
    average_daily_customers: Optional[int] = None
    average_daily_demand: Optional[int] = None
    current_suppliers: Optional[List[str]] = None
    alternative_suppliers: Optional[List[str]] = None
    accepts_emergency_deliveries: Optional[bool] = None
    priority_supply_requests: Optional[bool] = None


class PantryProfileUpdate(BaseModel):
    """Update pantry manager-specific profile fields."""
    pantry_name: Optional[str] = None
    organization_type: Optional[str] = None
    families_served: Optional[int] = None
    population_covered: Optional[int] = None
    food_requirements: Optional[List[str]] = None
    has_cold_storage: Optional[bool] = None
    warehouse_capacity: Optional[int] = None
    volunteer_count: Optional[int] = None
    vehicles_available: Optional[int] = None
    emergency_distribution_capacity: Optional[int] = None
    distribution_radius_km: Optional[float] = None


class AdminProfileUpdate(BaseModel):
    """Update admin-specific profile fields."""
    organization_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    authority_level: Optional[str] = None
    managed_regions: Optional[List[str]] = None
    managed_districts: Optional[List[str]] = None
    can_approve_routes: Optional[bool] = None
    can_broadcast_notifications: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me")
async def get_current_user_profile(current_user = Depends(get_current_user)) -> dict:
    """Fetch the current authenticated user's full profile (base + role-specific)."""
    # In production: call ProfileService.get_full_profile(current_user.id)
    return {
        "user_id": str(current_user.id),
        "base": {
            "full_name": current_user.user_metadata.get("full_name"),
            "email": current_user.email,
            "role": current_user.user_metadata.get("role", "viewer"),
        },
        "role_specific": {},
    }


@router.get("/{user_id}")
async def get_user_profile(
    user_id: UUID,
    current_user = Depends(get_current_user),
) -> dict:
    """Fetch a user's profile. Admin only or same user."""
    # In production: verify current_user is admin or requesting own profile
    # then call ProfileService.get_full_profile(user_id)
    return {}


@router.post("/update-base")
async def update_base_profile(
    payload: BaseProfileUpdate,
    current_user = Depends(get_current_user),
) -> dict:
    """Update current user's base profile fields."""
    # In production:
    # - Validate payload fields
    # - Update user_profiles table
    # - Return updated profile
    return {}


@router.post("/farmer/update")
async def update_farmer_profile(
    payload: FarmerProfileUpdate,
    current_user = Depends(get_current_user),
) -> dict:
    """Update current user's farmer profile. Farmer role only."""
    # In production:
    # - Verify role == "farmer"
    # - Upsert farmer_profiles table
    # - Update user_profiles.profile_complete flag
    # - Return updated profile
    return {}


@router.post("/driver/update")
async def update_driver_profile(
    payload: DriverProfileUpdate,
    current_user = Depends(get_current_user),
) -> dict:
    """Update current user's driver profile. Driver role only."""
    return {}


@router.post("/store/update")
async def update_store_profile(
    payload: StoreProfileUpdate,
    current_user = Depends(get_current_user),
) -> dict:
    """Update current user's store profile. Store owner role only."""
    return {}


@router.post("/pantry/update")
async def update_pantry_profile(
    payload: PantryProfileUpdate,
    current_user = Depends(get_current_user),
) -> dict:
    """Update current user's pantry profile. Pantry manager role only."""
    return {}


@router.post("/admin/update")
async def update_admin_profile(
    payload: AdminProfileUpdate,
    current_user = Depends(get_current_user),
) -> dict:
    """Update current user's admin profile. Admin role only."""
    return {}


@router.get("/discover/farmers")
async def discover_farmers(
    crop: Optional[str] = Query(None),
    crop_list: Optional[List[str]] = Query(None),
    min_quantity_kg: Optional[float] = Query(None),
    location_lat: Optional[float] = Query(None),
    location_lng: Optional[float] = Query(None),
    radius_km: Optional[float] = Query(None),
    trust_score_min: Optional[float] = Query(None),
    can_self_deliver: Optional[bool] = Query(None),
) -> dict:
    """Discover farmers matching criteria. Used by agents and store owners."""
    # In production:
    # - Call ProfileService.discover_farmers(crop_types=..., min_quantity_kg=..., location=..., ...)
    # - Return list of matching farmer profiles
    return {"farmers": []}


@router.get("/discover/drivers")
async def discover_drivers(
    vehicle_type: Optional[str] = Query(None),
    min_capacity_kg: Optional[float] = Query(None),
    location_lat: Optional[float] = Query(None),
    location_lng: Optional[float] = Query(None),
    max_radius_km: Optional[float] = Query(None),
    night_delivery: Optional[bool] = Query(None),
    flood_zone: Optional[bool] = Query(None),
    emergency_ready: Optional[bool] = Query(None),
) -> dict:
    """Discover drivers matching criteria. Used by agents for route optimization."""
    return {"drivers": []}


@router.get("/discover/stores")
async def discover_stores(
    category: Optional[str] = Query(None),
    category_list: Optional[List[str]] = Query(None),
    location_lat: Optional[float] = Query(None),
    location_lng: Optional[float] = Query(None),
    radius_km: Optional[float] = Query(None),
    min_daily_demand: Optional[int] = Query(None),
    cold_storage: Optional[bool] = Query(None),
    accepts_emergency: Optional[bool] = Query(None),
) -> dict:
    """Discover stores matching criteria. Used by agents for sourcing."""
    return {"stores": []}


@router.get("/discover/pantries")
async def discover_pantries(
    category: Optional[str] = Query(None),
    category_list: Optional[List[str]] = Query(None),
    location_lat: Optional[float] = Query(None),
    location_lng: Optional[float] = Query(None),
    radius_km: Optional[float] = Query(None),
    min_families_served: Optional[int] = Query(None),
) -> dict:
    """Discover pantries matching criteria. Used by agents for emergency distribution."""
    return {"pantries": []}
