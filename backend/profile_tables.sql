-- ============================================================
-- Role-specific profile tables for SupplyShield / Supabase
-- Run this file in Supabase to extend user profile storage and
-- create dedicated tables for farmers, drivers, stores, pantries,
-- and admins.
-- ============================================================

-- 1. Add shared profile metadata fields to the base user_profiles table.
ALTER TABLE IF EXISTS public.user_profiles
  ADD COLUMN IF NOT EXISTS address TEXT,
  ADD COLUMN IF NOT EXISTS latitude NUMERIC(9, 6),
  ADD COLUMN IF NOT EXISTS longitude NUMERIC(9, 6),
  ADD COLUMN IF NOT EXISTS availability_status TEXT,
  ADD COLUMN IF NOT EXISTS emergency_contact_name TEXT,
  ADD COLUMN IF NOT EXISTS emergency_contact_phone TEXT,
  ADD COLUMN IF NOT EXISTS emergency_contact_relationship TEXT,
  ADD COLUMN IF NOT EXISTS profile_complete BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS trust_score NUMERIC(5, 2) DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS trust_reviews INT DEFAULT 0;

COMMENT ON COLUMN public.user_profiles.address IS 'Primary address for the user or service location.';
COMMENT ON COLUMN public.user_profiles.latitude IS 'Location latitude for the user or service location.';
COMMENT ON COLUMN public.user_profiles.longitude IS 'Location longitude for the user or service location.';
COMMENT ON COLUMN public.user_profiles.availability_status IS 'Online / offline / on-duty status for the user.';
COMMENT ON COLUMN public.user_profiles.emergency_contact_name IS 'Emergency contact name for this user.';
COMMENT ON COLUMN public.user_profiles.emergency_contact_phone IS 'Emergency contact phone number.';
COMMENT ON COLUMN public.user_profiles.emergency_contact_relationship IS 'Relationship to emergency contact.';
COMMENT ON COLUMN public.user_profiles.profile_complete IS 'Flag indicating whether the user has completed their profile.';
COMMENT ON COLUMN public.user_profiles.trust_score IS 'Aggregate trust score for the profile based on deliveries and ratings.';
COMMENT ON COLUMN public.user_profiles.trust_reviews IS 'Number of trust or reliability reviews captured for the profile.';

-- 2. Farmer-specific profile table.
CREATE TABLE IF NOT EXISTS public.farmer_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID UNIQUE NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
  farm_name TEXT NOT NULL,
  farm_type TEXT NOT NULL DEFAULT 'conventional',
  crops_produced TEXT[],
  farm_size_acres NUMERIC(12, 2),
  production_capacity TEXT,
  available_quantity NUMERIC(12, 2),
  expected_harvest_date DATE,
  storage_availability TEXT,
  can_self_deliver BOOLEAN NOT NULL DEFAULT FALSE,
  max_delivery_distance_km NUMERIC(8, 2),
  organic_certification TEXT,
  government_registration_number TEXT,
  fssai_number TEXT,
  emergency_response_ready BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.farmer_profiles IS 'Detailed farmer profile data for SupplyShield AI operations.';

-- 3. Driver-specific profile table.
CREATE TABLE IF NOT EXISTS public.driver_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID UNIQUE NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
  vehicle_type TEXT NOT NULL DEFAULT 'motorcycle',
  vehicle_plate TEXT,
  max_load_kg NUMERIC(10, 2),
  vehicle_capacity_description TEXT,
  license_number TEXT,
  license_expiry DATE,
  vehicle_insurance_provider TEXT,
  insurance_valid_until DATE,
  permit_reference TEXT,
  current_latitude NUMERIC(9, 6),
  current_longitude NUMERIC(9, 6),
  operating_radius_km NUMERIC(8, 2),
  available_weekdays TEXT,
  night_delivery_allowed BOOLEAN NOT NULL DEFAULT FALSE,
  flood_zone_access BOOLEAN NOT NULL DEFAULT FALSE,
  emergency_ready BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.driver_profiles IS 'Detailed driver profile and logistics capabilities.';

-- 4. Store owner-specific profile table.
CREATE TABLE IF NOT EXISTS public.store_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID UNIQUE NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
  store_name TEXT NOT NULL,
  store_type TEXT NOT NULL DEFAULT 'retail',
  address TEXT,
  latitude NUMERIC(9, 6),
  longitude NUMERIC(9, 6),
  inventory_categories TEXT[],
  cold_storage_capacity NUMERIC(10, 2),
  average_daily_customers INT,
  average_daily_demand INT,
  current_suppliers TEXT[],
  alternative_suppliers TEXT[],
  accepts_emergency_deliveries BOOLEAN NOT NULL DEFAULT FALSE,
  priority_supply_requests BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.store_profiles IS 'Store owner profile metadata for supply chain demand and capacity.';

-- 5. Pantry manager-specific profile table.
CREATE TABLE IF NOT EXISTS public.pantry_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID UNIQUE NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
  pantry_name TEXT NOT NULL,
  organization_type TEXT NOT NULL DEFAULT 'community',
  families_served INT,
  population_covered INT,
  food_requirements TEXT[],
  has_cold_storage BOOLEAN NOT NULL DEFAULT FALSE,
  warehouse_capacity INT,
  volunteer_count INT,
  vehicles_available INT,
  emergency_distribution_capacity INT,
  distribution_radius_km NUMERIC(8, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.pantry_profiles IS 'Pantry manager profile for emergency distribution and community supply coordination.';

-- 6. Admin-specific profile table.
CREATE TABLE IF NOT EXISTS public.admin_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID UNIQUE NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
  organization_name TEXT,
  department TEXT,
  designation TEXT,
  authority_level TEXT NOT NULL DEFAULT 'regional',
  managed_regions TEXT[],
  managed_districts TEXT[],
  can_approve_routes BOOLEAN NOT NULL DEFAULT TRUE,
  can_broadcast_notifications BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.admin_profiles IS 'Admin profile records for system administrators, emergency coordinators and oversight roles.';

-- 7. Shared profile documents table for outgoing credentials and certifications.
CREATE TABLE IF NOT EXISTS public.profile_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
  document_type TEXT NOT NULL,
  document_url TEXT,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.profile_documents IS 'Optional document links and credential references for user profiles.';

-- 8. Optional profile location history table to record last known geography.
CREATE TABLE IF NOT EXISTS public.profile_locations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id UUID NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
  label TEXT,
  latitude NUMERIC(9, 6),
  longitude NUMERIC(9, 6),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.profile_locations IS 'Geographic points associated with a profile for logistics planning.';
