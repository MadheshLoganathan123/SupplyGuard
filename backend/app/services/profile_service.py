"""Profile service backed by Supabase tables."""

from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from app.database.supabase_client import supabase_admin


ROLE_TABLES = {
    "farmer": "farmer_profiles",
    "driver": "driver_profiles",
    "store_owner": "store_profiles",
    "pantry_manager": "pantry_profiles",
    "admin": "admin_profiles",
}

ROLE_ALIASES = {
    "admin": "admin",
    "farmer": "farmer",
    "driver": "driver",
    "store owner": "store_owner",
    "store_owner": "store_owner",
    "store_manager": "store_owner",
    "pantry manager": "pantry_manager",
    "pantry_manager": "pantry_manager",
    "viewer": "viewer",
}


class ProfileService:
    """Service for CRUD and discovery across user and role-specific profiles."""

    def __init__(self, db_session: Any = None) -> None:
        self.db = db_session
        self.client = supabase_admin

    @staticmethod
    def normalize_role(role: Any) -> str:
        raw = getattr(role, "value", role)
        key = str(raw or "viewer").strip().lower().replace("-", "_")
        key = key.replace("_", " ")
        return ROLE_ALIASES.get(key, key.replace(" ", "_"))

    @staticmethod
    def _clean_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in payload.items() if value is not None}

    @staticmethod
    def _one(result: Any) -> Optional[Dict[str, Any]]:
        data = getattr(result, "data", None)
        if isinstance(data, list):
            return data[0] if data else None
        return data

    @staticmethod
    def _many(result: Any) -> List[Dict[str, Any]]:
        data = getattr(result, "data", None)
        if data is None:
            return []
        return data if isinstance(data, list) else [data]

    @staticmethod
    def _contains_any(values: Any, candidates: Optional[Iterable[str]]) -> bool:
        if not candidates:
            return True
        source = {str(value).strip().lower() for value in (values or [])}
        wanted = {str(value).strip().lower() for value in candidates if value}
        return bool(source & wanted)

    @staticmethod
    def _distance_km(a_lat: Any, a_lng: Any, b_lat: float, b_lng: float) -> Optional[float]:
        if a_lat is None or a_lng is None:
            return None
        lat1, lng1, lat2, lng2 = map(radians, [float(a_lat), float(a_lng), b_lat, b_lng])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        return 6371.0 * 2 * asin(sqrt(h))

    def _select_by_auth_id(self, table: str, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        result = self.client.table(table).select("*").eq("auth_id", str(user_id)).maybe_single().execute()
        return self._one(result)

    def _upsert_by_auth_id(self, table: str, user_id: UUID | str, payload: Dict[str, Any]) -> Dict[str, Any]:
        clean = self._clean_payload({"auth_id": str(user_id), **payload})
        result = self.client.table(table).upsert(clean, on_conflict="auth_id").execute()
        row = self._one(result)
        if row is None:
            row = self._select_by_auth_id(table, user_id)
        return row or clean

    async def get_base_profile(self, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        return self._select_by_auth_id("user_profiles", user_id)

    async def update_base_profile(self, user_id: UUID | str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._upsert_by_auth_id("user_profiles", user_id, payload)

    async def get_farmer_profile(self, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        return self._select_by_auth_id("farmer_profiles", user_id)

    async def get_driver_profile(self, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        return self._select_by_auth_id("driver_profiles", user_id)

    async def get_store_profile(self, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        return self._select_by_auth_id("store_profiles", user_id)

    async def get_pantry_profile(self, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        return self._select_by_auth_id("pantry_profiles", user_id)

    async def get_admin_profile(self, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        return self._select_by_auth_id("admin_profiles", user_id)

    async def get_role_profile(self, role: str, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        table = ROLE_TABLES.get(self.normalize_role(role))
        return self._select_by_auth_id(table, user_id) if table else None

    async def update_role_profile(self, role: str, user_id: UUID | str, payload: Dict[str, Any]) -> Dict[str, Any]:
        table = ROLE_TABLES.get(self.normalize_role(role))
        if not table:
            raise ValueError(f"Role {role!r} does not have a role-specific profile table")
        row = self._upsert_by_auth_id(table, user_id, payload)
        self.client.table("user_profiles").update({"profile_complete": True}).eq("auth_id", str(user_id)).execute()
        return row

    async def get_full_profile(self, user_id: UUID | str) -> Optional[Dict[str, Any]]:
        base = await self.get_base_profile(user_id)
        if not base:
            return None
        role_data = await self.get_role_profile(base.get("role", "viewer"), user_id)
        return {"base": base, "role_specific": role_data or {}}

    def _base_profile_map(self, auth_ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        ids = [str(auth_id) for auth_id in auth_ids if auth_id]
        if not ids:
            return {}
        result = self.client.table("user_profiles").select("*").in_("auth_id", ids).execute()
        return {str(row["auth_id"]): row for row in self._many(result)}

    def _join_base_profiles(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        profiles = self._base_profile_map(row.get("auth_id") for row in rows)
        return [{**row, "user_profile": profiles.get(str(row.get("auth_id")), {})} for row in rows]

    async def discover_farmers(
        self,
        crop_types: Optional[List[str]] = None,
        min_quantity_kg: Optional[float] = None,
        location: Optional[tuple[float, float]] = None,
        radius_km: Optional[float] = None,
        trust_score_threshold: Optional[float] = None,
        can_self_deliver: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._many(self.client.table("farmer_profiles").select("*").execute())
        matches = []
        for row in self._join_base_profiles(rows):
            base = row.get("user_profile", {})
            distance = None
            if location and radius_km is not None:
                distance = self._distance_km(base.get("latitude"), base.get("longitude"), *location)
                if distance is None or distance > radius_km:
                    continue
            if not self._contains_any(row.get("crops_produced"), crop_types):
                continue
            if min_quantity_kg is not None and float(row.get("available_quantity") or 0) < min_quantity_kg:
                continue
            if trust_score_threshold is not None and float(base.get("trust_score") or 0) < trust_score_threshold:
                continue
            if can_self_deliver is not None and row.get("can_self_deliver") is not can_self_deliver:
                continue
            matches.append({**row, "distance_km": distance})
        return matches

    async def discover_drivers(
        self,
        vehicle_types: Optional[List[str]] = None,
        min_capacity_kg: Optional[float] = None,
        location: Optional[tuple[float, float]] = None,
        max_radius_km: Optional[float] = None,
        night_delivery: Optional[bool] = None,
        flood_zone_capable: Optional[bool] = None,
        emergency_ready: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._many(self.client.table("driver_profiles").select("*").execute())
        matches = []
        for row in self._join_base_profiles(rows):
            distance = None
            if location and max_radius_km is not None:
                distance = self._distance_km(row.get("current_latitude"), row.get("current_longitude"), *location)
                if distance is None or distance > max_radius_km:
                    continue
                if row.get("operating_radius_km") and distance > float(row["operating_radius_km"]):
                    continue
            if vehicle_types and str(row.get("vehicle_type", "")).lower() not in {v.lower() for v in vehicle_types}:
                continue
            if min_capacity_kg is not None and float(row.get("max_load_kg") or 0) < min_capacity_kg:
                continue
            if night_delivery is not None and row.get("night_delivery_allowed") is not night_delivery:
                continue
            if flood_zone_capable is not None and row.get("flood_zone_access") is not flood_zone_capable:
                continue
            if emergency_ready is not None and row.get("emergency_ready") is not emergency_ready:
                continue
            matches.append({**row, "distance_km": distance})
        return matches

    async def discover_stores(
        self,
        inventory_categories: Optional[List[str]] = None,
        location: Optional[tuple[float, float]] = None,
        radius_km: Optional[float] = None,
        min_daily_demand: Optional[int] = None,
        cold_storage_required: Optional[bool] = None,
        accepts_emergency: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._many(self.client.table("store_profiles").select("*").execute())
        matches = []
        for row in self._join_base_profiles(rows):
            distance = None
            lat = row.get("latitude") or row.get("user_profile", {}).get("latitude")
            lng = row.get("longitude") or row.get("user_profile", {}).get("longitude")
            if location and radius_km is not None:
                distance = self._distance_km(lat, lng, *location)
                if distance is None or distance > radius_km:
                    continue
            if not self._contains_any(row.get("inventory_categories"), inventory_categories):
                continue
            if min_daily_demand is not None and int(row.get("average_daily_demand") or 0) < min_daily_demand:
                continue
            if cold_storage_required and not row.get("cold_storage_capacity"):
                continue
            if accepts_emergency is not None and row.get("accepts_emergency_deliveries") is not accepts_emergency:
                continue
            matches.append({**row, "distance_km": distance})
        return matches

    async def discover_pantries(
        self,
        food_categories: Optional[List[str]] = None,
        min_families_served: Optional[int] = None,
        location: Optional[tuple[float, float]] = None,
        radius_km: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._many(self.client.table("pantry_profiles").select("*").execute())
        matches = []
        for row in self._join_base_profiles(rows):
            distance = None
            base = row.get("user_profile", {})
            if location and radius_km is not None:
                distance = self._distance_km(base.get("latitude"), base.get("longitude"), *location)
                if distance is None or distance > radius_km:
                    continue
            if not self._contains_any(row.get("food_requirements"), food_categories):
                continue
            if min_families_served is not None and int(row.get("families_served") or 0) < min_families_served:
                continue
            matches.append({**row, "distance_km": distance})
        return matches

    async def enrich_shipment_with_profiles(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        return shipment

    async def enrich_incident_with_profiles(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        return incident

    async def compute_matching_score(self, farmer: Dict[str, Any], store: Dict[str, Any]) -> float:
        farmer_crops = set(farmer.get("crops_produced") or [])
        store_categories = set(store.get("inventory_categories") or [])
        overlap = 1.0 if farmer_crops & store_categories else 0.4
        quantity = min(float(farmer.get("available_quantity") or 0) / max(float(store.get("average_daily_demand") or 1), 1), 1)
        trust = min(float(farmer.get("user_profile", {}).get("trust_score") or 0) / 100, 1)
        return round((overlap * 0.45) + (quantity * 0.35) + (trust * 0.20), 3)
