"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { User } from "@supabase/supabase-js";
import { supabase } from "../../lib/supabaseClient";

const roleLabels: Record<string, string> = {
  admin: "Admin",
  farmer: "Farmer",
  driver: "Driver",
  store_owner: "Store Owner",
  pantry_manager: "Pantry Manager",
  viewer: "Viewer",
};

const initialBaseProfile = {
  full_name: "",
  email: "",
  phone: "",
  role: "viewer",
  address: "",
  latitude: "",
  longitude: "",
  availability_status: "online",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  emergency_contact_relationship: "",
  additional_credentials: "",
  profile_complete: false,
};

const initialRoleData = {
  farmer: {
    farm_name: "",
    farm_type: "conventional",
    crops_produced: "",
    farm_size_acres: "",
    production_capacity: "",
    available_quantity: "",
    expected_harvest_date: "",
    storage_availability: "",
    can_self_deliver: false,
    max_delivery_distance_km: "",
    organic_certification: "",
    government_registration_number: "",
    fssai_number: "",
    emergency_response_ready: false,
  },
  driver: {
    vehicle_type: "motorcycle",
    vehicle_plate: "",
    max_load_kg: "",
    vehicle_capacity_description: "",
    license_number: "",
    license_expiry: "",
    vehicle_insurance_provider: "",
    insurance_valid_until: "",
    permit_reference: "",
    current_latitude: "",
    current_longitude: "",
    operating_radius_km: "",
    available_weekdays: "",
    night_delivery_allowed: false,
    flood_zone_access: false,
    emergency_ready: false,
  },
  store_owner: {
    store_name: "",
    store_type: "retail",
    inventory_categories: "",
    cold_storage_capacity: "",
    average_daily_customers: "",
    average_daily_demand: "",
    current_suppliers: "",
    alternative_suppliers: "",
    accepts_emergency_deliveries: false,
    priority_supply_requests: false,
  },
  pantry_manager: {
    pantry_name: "",
    organization_type: "community",
    families_served: "",
    population_covered: "",
    food_requirements: "",
    has_cold_storage: false,
    warehouse_capacity: "",
    volunteer_count: "",
    vehicles_available: "",
    emergency_distribution_capacity: "",
    distribution_radius_km: "",
  },
  admin: {
    organization_name: "",
    department: "",
    designation: "",
    authority_level: "regional",
    managed_regions: "",
    managed_districts: "",
    can_approve_routes: true,
    can_broadcast_notifications: true,
  },
};

const roleTableMap: Record<string, string | null> = {
  admin: "admin_profiles",
  farmer: "farmer_profiles",
  driver: "driver_profiles",
  store_owner: "store_profiles",
  pantry_manager: "pantry_profiles",
  viewer: null,
};

const normalizeRole = (value?: string) => {
  if (!value) return "viewer";
  const normalized = value.toString().trim().toLowerCase().replace(/\s+/g, "_");
  const validRoles = ["admin", "farmer", "driver", "store_owner", "pantry_manager", "viewer"];
  return validRoles.includes(normalized) ? normalized : "viewer";
};

type BaseProfile = {
  full_name: string;
  email: string;
  phone: string;
  role: string;
  address: string;
  latitude: string;
  longitude: string;
  availability_status: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relationship: string;
  additional_credentials: string;
  profile_complete: boolean;
};

type RoleData = Record<string, string | boolean>;

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [sessionUser, setSessionUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<BaseProfile>(initialBaseProfile);
  const [roleData, setRoleData] = useState<RoleData>(initialRoleData.farmer);

  const roleLabel = roleLabels[profile.role] || profile.role || "Viewer";
  const roleTable = roleTableMap[profile.role] || null;

  const parseNumber = (value: string | number | null | undefined) => {
    if (value === null || value === undefined || value === "") return null;
    const parsed = Number(String(value).replace(/,/g, ""));
    return Number.isFinite(parsed) ? parsed : null;
  };

  const asArray = (value: string | string[] | null | undefined) => {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    return String(value)
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  };

  const loadProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const {
        data: { session },
        error: sessionError,
      } = await supabase.auth.getSession();

      if (sessionError) throw sessionError;
      if (!session?.user) {
        setError("Please sign in to access your profile.");
        setLoading(false);
        return;
      }

      setSessionUser(session.user);
      const authId = session.user.id;
      const profileQuery = await supabase
        .from("user_profiles")
        .select(
          "full_name, email, role, phone, address, latitude, longitude, availability_status, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, additional_credentials, profile_complete"
        )
        .eq("auth_id", authId)
        .maybeSingle();

      if (profileQuery.error) throw profileQuery.error;

      const row = profileQuery.data;
      const resolvedRole = normalizeRole(row?.role || session.user.user_metadata?.role);

      setProfile({
        ...initialBaseProfile,
        full_name: row?.full_name || session.user.user_metadata?.full_name || "",
        email: row?.email || session.user.email || "",
        phone: row?.phone || "",
        role: resolvedRole,
        address: row?.address || "",
        latitude: row?.latitude ? String(row.latitude) : "",
        longitude: row?.longitude ? String(row.longitude) : "",
        availability_status: row?.availability_status || "online",
        emergency_contact_name: row?.emergency_contact_name || "",
        emergency_contact_phone: row?.emergency_contact_phone || "",
        emergency_contact_relationship: row?.emergency_contact_relationship || "",
        additional_credentials: row?.additional_credentials || "",
        profile_complete: Boolean(row?.profile_complete),
      });

      const roleTableName = roleTableMap[resolvedRole];
      if (roleTableName) {
        const roleQuery = await supabase
          .from(roleTableName)
          .select("*")
          .eq("auth_id", authId)
          .maybeSingle();

        if (roleQuery.error) throw roleQuery.error;

        if (roleQuery.data) {
          const savedData = roleQuery.data;
          const allowedKeys = Object.keys(initialRoleData[resolvedRole] || {});
          setRoleData((prev: RoleData) => ({
            ...prev,
            ...Object.fromEntries(
              Object.entries(savedData)
                .filter(([key]) => allowedKeys.includes(key))
                .map(([key, value]) => [
                  key,
                  Array.isArray(value) ? value.join(", ") : value ?? "",
                ])
            ),
          }));
        } else {
          setRoleData(initialRoleData[resolvedRole] || initialRoleData.farmer);
        }
      } else {
        setRoleData(initialRoleData.farmer);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const runLoadProfile = async () => {
      await loadProfile();
    };
    void runLoadProfile();
  }, []);

  const validateRequiredFields = () => {
    const requiredMap: Record<string, string[]> = {
      farmer: [
        "farm_name",
        "farm_type",
        "crops_produced",
        "farm_size_acres",
        "available_quantity",
        "storage_availability",
      ],
      driver: [
        "vehicle_type",
        "max_load_kg",
        "license_number",
        "license_expiry",
        "operating_radius_km",
      ],
      store_owner: [
        "store_name",
        "store_type",
        "inventory_categories",
        "average_daily_customers",
        "current_suppliers",
      ],
      pantry_manager: [
        "pantry_name",
        "organization_type",
        "families_served",
        "population_covered",
        "food_requirements",
      ],
      admin: ["organization_name", "department", "designation", "authority_level"],
      viewer: [],
    };

    const requiredKeys = requiredMap[profile.role] || [];
    const missing = requiredKeys.filter((key) => {
      const value = roleData[key];
      return value === undefined || value === null || String(value).trim() === "";
    });

    return missing;
  };

  const renderRoleSection = () => {
    if (!profile.role || profile.role === "viewer") {
      return (
        <div className="rounded-xl border border-outline-variant/20 bg-surface-container p-md">
          <p className="text-sm text-on-surface-variant">
            Your account is currently a generic viewer profile. Complete a role-specific signup flow to unlock farmer, driver, store owner, pantry manager, or admin profile details.
          </p>
        </div>
      );
    }

    switch (profile.role) {
      case "farmer":
        return (
          <div className="space-y-md rounded-xl border border-outline-variant/20 bg-surface-container p-md">
            <h2 className="text-lg font-semibold">Farmer Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Farm name</span>
                <input
                  type="text"
                  value={roleData.farm_name}
                  onChange={(e) => setRoleData({ ...roleData, farm_name: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Farm type</span>
                <input
                  type="text"
                  value={roleData.farm_type}
                  onChange={(e) => setRoleData({ ...roleData, farm_type: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Crops produced</span>
                <input
                  type="text"
                  value={roleData.crops_produced}
                  onChange={(e) => setRoleData({ ...roleData, crops_produced: e.target.value })}
                  placeholder="Rice, Wheat, Tomatoes"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Farm size (acres)</span>
                <input
                  type="number"
                  value={roleData.farm_size_acres}
                  onChange={(e) => setRoleData({ ...roleData, farm_size_acres: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Available quantity</span>
                <input
                  type="text"
                  value={roleData.available_quantity}
                  onChange={(e) => setRoleData({ ...roleData, available_quantity: e.target.value })}
                  placeholder="2000 kg"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Storage availability</span>
                <input
                  type="text"
                  value={roleData.storage_availability}
                  onChange={(e) => setRoleData({ ...roleData, storage_availability: e.target.value })}
                  placeholder="Cold storage available / On-farm storage"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Can self-deliver</span>
                <select
                  value={roleData.can_self_deliver ? "yes" : "no"}
                  onChange={(e) => setRoleData({ ...roleData, can_self_deliver: e.target.value === "yes" })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Max delivery distance (km)</span>
                <input
                  type="number"
                  value={roleData.max_delivery_distance_km}
                  onChange={(e) => setRoleData({ ...roleData, max_delivery_distance_km: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Certifications / registration</span>
                <input
                  type="text"
                  value={roleData.organic_certification}
                  onChange={(e) => setRoleData({ ...roleData, organic_certification: e.target.value })}
                  placeholder="Organic / Govt registration info"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Government IDs</span>
                <input
                  type="text"
                  value={roleData.government_registration_number}
                  onChange={(e) => setRoleData({ ...roleData, government_registration_number: e.target.value })}
                  placeholder="GST / registration / FSSAI"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
          </div>
        );
      case "driver":
        return (
          <div className="space-y-md rounded-xl border border-outline-variant/20 bg-surface-container p-md">
            <h2 className="text-lg font-semibold">Driver Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Vehicle type</span>
                <input
                  type="text"
                  value={roleData.vehicle_type}
                  onChange={(e) => setRoleData({ ...roleData, vehicle_type: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Vehicle plate</span>
                <input
                  type="text"
                  value={roleData.vehicle_plate}
                  onChange={(e) => setRoleData({ ...roleData, vehicle_plate: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Maximum load (kg)</span>
                <input
                  type="number"
                  value={roleData.max_load_kg}
                  onChange={(e) => setRoleData({ ...roleData, max_load_kg: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Cargo capacity notes</span>
                <input
                  type="text"
                  value={roleData.vehicle_capacity_description}
                  onChange={(e) => setRoleData({ ...roleData, vehicle_capacity_description: e.target.value })}
                  placeholder="e.g. 8m3 insulated trailer"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">License number</span>
                <input
                  type="text"
                  value={roleData.license_number}
                  onChange={(e) => setRoleData({ ...roleData, license_number: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">License expiry</span>
                <input
                  type="date"
                  value={roleData.license_expiry}
                  onChange={(e) => setRoleData({ ...roleData, license_expiry: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Insurance provider</span>
                <input
                  type="text"
                  value={roleData.vehicle_insurance_provider}
                  onChange={(e) => setRoleData({ ...roleData, vehicle_insurance_provider: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Insurance valid until</span>
                <input
                  type="date"
                  value={roleData.insurance_valid_until}
                  onChange={(e) => setRoleData({ ...roleData, insurance_valid_until: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Operating radius (km)</span>
                <input
                  type="number"
                  value={roleData.operating_radius_km}
                  onChange={(e) => setRoleData({ ...roleData, operating_radius_km: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Available weekdays</span>
                <input
                  type="text"
                  value={roleData.available_weekdays}
                  onChange={(e) => setRoleData({ ...roleData, available_weekdays: e.target.value })}
                  placeholder="Mon-Fri / 24x7"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Night delivery allowed</span>
                <select
                  value={roleData.night_delivery_allowed ? "yes" : "no"}
                  onChange={(e) => setRoleData({ ...roleData, night_delivery_allowed: e.target.value === "yes" })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Flood zone access</span>
                <select
                  value={roleData.flood_zone_access ? "yes" : "no"}
                  onChange={(e) => setRoleData({ ...roleData, flood_zone_access: e.target.value === "yes" })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
            </div>
          </div>
        );
      case "store_owner":
        return (
          <div className="space-y-md rounded-xl border border-outline-variant/20 bg-surface-container p-md">
            <h2 className="text-lg font-semibold">Store Owner Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Store name</span>
                <input
                  type="text"
                  value={roleData.store_name}
                  onChange={(e) => setRoleData({ ...roleData, store_name: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Store type</span>
                <input
                  type="text"
                  value={roleData.store_type}
                  onChange={(e) => setRoleData({ ...roleData, store_type: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Inventory categories</span>
                <input
                  type="text"
                  value={roleData.inventory_categories}
                  onChange={(e) => setRoleData({ ...roleData, inventory_categories: e.target.value })}
                  placeholder="Fruit, Dairy, Staples"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Cold storage capacity (kg)</span>
                <input
                  type="number"
                  value={roleData.cold_storage_capacity}
                  onChange={(e) => setRoleData({ ...roleData, cold_storage_capacity: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Average daily customers</span>
                <input
                  type="number"
                  value={roleData.average_daily_customers}
                  onChange={(e) => setRoleData({ ...roleData, average_daily_customers: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Current suppliers</span>
                <input
                  type="text"
                  value={roleData.current_suppliers}
                  onChange={(e) => setRoleData({ ...roleData, current_suppliers: e.target.value })}
                  placeholder="Supplier A, Supplier B"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Alternative suppliers</span>
                <input
                  type="text"
                  value={roleData.alternative_suppliers}
                  onChange={(e) => setRoleData({ ...roleData, alternative_suppliers: e.target.value })}
                  placeholder="Backup supplier names"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Accept emergency deliveries</span>
                <select
                  value={roleData.accepts_emergency_deliveries ? "yes" : "no"}
                  onChange={(e) => setRoleData({ ...roleData, accepts_emergency_deliveries: e.target.value === "yes" })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
            </div>
          </div>
        );
      case "pantry_manager":
        return (
          <div className="space-y-md rounded-xl border border-outline-variant/20 bg-surface-container p-md">
            <h2 className="text-lg font-semibold">Pantry Manager Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Pantry name</span>
                <input
                  type="text"
                  value={roleData.pantry_name}
                  onChange={(e) => setRoleData({ ...roleData, pantry_name: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Organization type</span>
                <input
                  type="text"
                  value={roleData.organization_type}
                  onChange={(e) => setRoleData({ ...roleData, organization_type: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Families served</span>
                <input
                  type="number"
                  value={roleData.families_served}
                  onChange={(e) => setRoleData({ ...roleData, families_served: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Population covered</span>
                <input
                  type="number"
                  value={roleData.population_covered}
                  onChange={(e) => setRoleData({ ...roleData, population_covered: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <label className="block">
              <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Food requirements</span>
              <input
                type="text"
                value={roleData.food_requirements}
                onChange={(e) => setRoleData({ ...roleData, food_requirements: e.target.value })}
                placeholder="Rice, canned goods, fresh vegetables"
                className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                required
              />
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Warehouse capacity</span>
                <input
                  type="number"
                  value={roleData.warehouse_capacity}
                  onChange={(e) => setRoleData({ ...roleData, warehouse_capacity: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Volunteer count</span>
                <input
                  type="number"
                  value={roleData.volunteer_count}
                  onChange={(e) => setRoleData({ ...roleData, volunteer_count: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
          </div>
        );
      case "admin":
        return (
          <div className="space-y-md rounded-xl border border-outline-variant/20 bg-surface-container p-md">
            <h2 className="text-lg font-semibold">Admin Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Organization name</span>
                <input
                  type="text"
                  value={roleData.organization_name}
                  onChange={(e) => setRoleData({ ...roleData, organization_name: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Department</span>
                <input
                  type="text"
                  value={roleData.department}
                  onChange={(e) => setRoleData({ ...roleData, department: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Designation</span>
                <input
                  type="text"
                  value={roleData.designation}
                  onChange={(e) => setRoleData({ ...roleData, designation: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Authority level</span>
                <input
                  type="text"
                  value={roleData.authority_level}
                  onChange={(e) => setRoleData({ ...roleData, authority_level: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>
            <label className="block">
              <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Managed regions</span>
              <input
                type="text"
                value={roleData.managed_regions}
                onChange={(e) => setRoleData({ ...roleData, managed_regions: e.target.value })}
                placeholder="District 1, Zone A"
                className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </label>
          </div>
        );
      default:
        return null;
    }
  };

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      if (!sessionUser) {
        throw new Error("Unable to save profile: no authenticated user.");
      }

      const missingRoleFields = validateRequiredFields();
      if (missingRoleFields.length > 0) {
        throw new Error(`Please complete all required ${roleLabel} fields: ${missingRoleFields.join(", ")}`);
      }

      const profilePayload = {
        auth_id: sessionUser.id,
        full_name: profile.full_name.trim(),
        email: profile.email.trim(),
        phone: profile.phone.trim() || null,
        address: profile.address.trim() || null,
        latitude: parseNumber(profile.latitude),
        longitude: parseNumber(profile.longitude),
        availability_status: profile.availability_status.trim() || null,
        emergency_contact_name: profile.emergency_contact_name.trim() || null,
        emergency_contact_phone: profile.emergency_contact_phone.trim() || null,
        emergency_contact_relationship: profile.emergency_contact_relationship.trim() || null,
        additional_credentials: profile.additional_credentials.trim() || null,
        role: profile.role,
        profile_complete: missingRoleFields.length === 0,
      };

      const { error: profileError } = await supabase
        .from("user_profiles")
        .upsert(profilePayload, { onConflict: "auth_id" });

      if (profileError) {
        throw profileError;
      }

      if (roleTable) {
        const allowedKeys = Object.keys(initialRoleData[profile.role] || {});
        const rolePayload: Record<string, unknown> = {
          auth_id: sessionUser.id,
          ...Object.fromEntries(
            Object.entries(roleData)
              .filter(([key]) => allowedKeys.includes(key))
              .map(([key, value]) => {
                if (typeof value === "boolean") return [key, value];
                if (key.endsWith("_categories") || key.endsWith("_suppliers") || key.endsWith("_regions") || key.endsWith("_districts") || key === "crops_produced" || key === "food_requirements") {
                  return [key, asArray(value)];
                }
                if (key.startsWith("max_") || key.endsWith("_kg") || key.endsWith("_capacity") || key.endsWith("_radius_km") || key.endsWith("_per_day") || key.endsWith("_served") || key.endsWith("_covered") || key.endsWith("_count") || key.endsWith("_available")) {
                  return [key, parseNumber(value)];
                }
                return [key, value || null];
              })
          ),
        };

        const { error: roleError } = await supabase
          .from(roleTable)
          .upsert(rolePayload, { onConflict: "auth_id" });

        if (roleError) {
          throw roleError;
        }
      }

      setSuccess("Profile saved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pt-[88px] pb-20 flex-1 flex flex-col px-lg py-md gap-md overflow-y-auto h-full">
      <div className="flex flex-col gap-md max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-start gap-sm">
          <div>
            <h1 className="text-[26px] font-bold text-on-surface leading-tight tracking-tight">Profile</h1>
            <p className="text-[12px] text-on-surface-variant mt-[3px]">Complete role-specific profile information for AI logistics, sourcing, and response coordination.</p>
          </div>
          <Link href="/" className="text-primary text-[12px] font-semibold hover:underline">Back to dashboard</Link>
        </div>

        <div className="glass-panel rounded-xl p-md space-y-md">
          <div className="flex flex-wrap gap-md mb-md">
            <div className="min-w-[220px] rounded-xl bg-surface-container border border-outline-variant/20 p-md flex-1">
              <p className="text-[10px] uppercase tracking-[0.25em] text-on-surface-variant font-mono mb-2">Signed in as</p>
              <p className="text-[16px] font-bold text-on-surface">{sessionUser?.email || "—"}</p>
              <p className="text-[11px] text-on-surface-variant mt-2">Role: {roleLabel}</p>
            </div>
            <div className="min-w-[220px] rounded-xl bg-surface-container border border-outline-variant/20 p-md flex-1">
              <p className="text-[10px] uppercase tracking-[0.25em] text-on-surface-variant font-mono mb-2">Profile status</p>
              <p className="text-[13px] font-semibold text-on-surface">{loading ? "Loading…" : profile.profile_complete ? "Complete" : "Incomplete"}</p>
            </div>
          </div>

          <form onSubmit={handleSave} className="space-y-md">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Full name</span>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Email address</span>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Phone</span>
                <input
                  type="tel"
                  value={profile.phone}
                  onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  required
                />
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Role</span>
                <input
                  type="text"
                  value={roleLabel}
                  readOnly
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-surface-container text-sm px-4 py-3 outline-none"
                />
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Location address</span>
                <input
                  type="text"
                  value={profile.address}
                  onChange={(e) => setProfile({ ...profile, address: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
              <div className="grid grid-cols-2 gap-md">
                <label className="block">
                  <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Latitude</span>
                  <input
                    type="number"
                    step="0.000001"
                    value={profile.latitude}
                    onChange={(e) => setProfile({ ...profile, latitude: e.target.value })}
                    className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </label>
                <label className="block">
                  <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Longitude</span>
                  <input
                    type="number"
                    step="0.000001"
                    value={profile.longitude}
                    onChange={(e) => setProfile({ ...profile, longitude: e.target.value })}
                    className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </label>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Availability status</span>
                <select
                  value={profile.availability_status}
                  onChange={(e) => setProfile({ ...profile, availability_status: e.target.value })}
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                  <option value="on_duty">On duty</option>
                </select>
              </label>
              <label className="block">
                <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Emergency contact</span>
                <input
                  type="text"
                  value={profile.emergency_contact_name}
                  onChange={(e) => setProfile({ ...profile, emergency_contact_name: e.target.value })}
                  placeholder="Name, phone, relationship"
                  className="mt-2 w-full rounded-lg border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>

            {renderRoleSection()}

            <label className="block">
              <span className="text-[11px] text-on-surface-variant uppercase tracking-[0.2em] font-bold">Additional credentials</span>
              <textarea
                value={profile.additional_credentials}
                onChange={(e) => setProfile({ ...profile, additional_credentials: e.target.value })}
                className="mt-2 w-full min-h-[140px] rounded-xl border border-outline-variant/30 bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter certifications, licenses, certifications, or important notes..."
              />
            </label>

            {(error || success) && (
              <div className={`rounded-xl border px-4 py-3 text-sm ${error ? "bg-error/10 border-error/20 text-error" : "bg-primary/10 border-primary/20 text-primary"}`}>
                {error || success}
              </div>
            )}

            <button
              type="submit"
              disabled={saving || loading}
              className="inline-flex items-center justify-center rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-on-primary transition hover:brightness-110 disabled:opacity-60"
            >
              {saving ? "Saving…" : "Save Profile"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
