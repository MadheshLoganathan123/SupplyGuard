"""Unified profiles, reroute jobs, and user actions.

Revision ID: 0001_profiles_jobs_actions
Revises:
Create Date: 2026-06-19
"""

from alembic import op


revision = "0001_profiles_jobs_actions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.user_profiles (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            auth_id UUID UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            address TEXT,
            latitude NUMERIC(9, 6),
            longitude NUMERIC(9, 6),
            availability_status TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relationship TEXT,
            profile_complete BOOLEAN NOT NULL DEFAULT FALSE,
            trust_score NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
            trust_reviews INT NOT NULL DEFAULT 0,
            additional_credentials TEXT,
            role TEXT NOT NULL DEFAULT 'viewer'
                CHECK (role IN ('admin','farmer','driver','store_owner','pantry_manager','viewer')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        ALTER TABLE IF EXISTS public.user_profiles
            ADD COLUMN IF NOT EXISTS phone TEXT,
            ADD COLUMN IF NOT EXISTS address TEXT,
            ADD COLUMN IF NOT EXISTS latitude NUMERIC(9, 6),
            ADD COLUMN IF NOT EXISTS longitude NUMERIC(9, 6),
            ADD COLUMN IF NOT EXISTS availability_status TEXT,
            ADD COLUMN IF NOT EXISTS emergency_contact_name TEXT,
            ADD COLUMN IF NOT EXISTS emergency_contact_phone TEXT,
            ADD COLUMN IF NOT EXISTS emergency_contact_relationship TEXT,
            ADD COLUMN IF NOT EXISTS profile_complete BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS trust_score NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS trust_reviews INT NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS additional_credentials TEXT,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

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

        CREATE TABLE IF NOT EXISTS public.profile_documents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            auth_id UUID NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
            document_type TEXT NOT NULL,
            document_url TEXT,
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS public.profile_locations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            auth_id UUID NOT NULL REFERENCES public.user_profiles(auth_id) ON DELETE CASCADE,
            label TEXT,
            latitude NUMERIC(9, 6),
            longitude NUMERIC(9, 6),
            recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.reroute_jobs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            shipment_id UUID,
            requested_by UUID,
            status TEXT NOT NULL DEFAULT 'queued'
                CHECK (status IN ('queued','running','completed','failed','cancelled')),
            reason TEXT,
            input JSONB NOT NULL DEFAULT '{}',
            result JSONB,
            agent_name TEXT,
            confidence NUMERIC(4, 3) CHECK (confidence BETWEEN 0 AND 1),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS public.user_actions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            auth_id UUID,
            action_type TEXT NOT NULL,
            entity_type TEXT,
            entity_id UUID,
            payload JSONB NOT NULL DEFAULT '{}',
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_user_profiles_auth_id ON public.user_profiles(auth_id);
        CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);
        CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON public.user_profiles(role);
        CREATE INDEX IF NOT EXISTS idx_farmer_profiles_auth_id ON public.farmer_profiles(auth_id);
        CREATE INDEX IF NOT EXISTS idx_driver_profiles_auth_id ON public.driver_profiles(auth_id);
        CREATE INDEX IF NOT EXISTS idx_store_profiles_auth_id ON public.store_profiles(auth_id);
        CREATE INDEX IF NOT EXISTS idx_pantry_profiles_auth_id ON public.pantry_profiles(auth_id);
        CREATE INDEX IF NOT EXISTS idx_reroute_jobs_status ON public.reroute_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_reroute_jobs_created_at ON public.reroute_jobs(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_user_actions_auth_id ON public.user_actions(auth_id);
        CREATE INDEX IF NOT EXISTS idx_user_actions_created_at ON public.user_actions(created_at DESC);
        """
    )
    for table in (
        "user_profiles",
        "farmer_profiles",
        "driver_profiles",
        "store_profiles",
        "pantry_profiles",
        "admin_profiles",
        "reroute_jobs",
    ):
        op.execute(
            f"""
            DROP TRIGGER IF EXISTS trg_{table}_updated_at ON public.{table};
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON public.{table}
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
            ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;
            """
        )
    op.execute("ALTER TABLE public.profile_documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.profile_locations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.user_actions ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_profiles' AND policyname = 'profiles_read_own') THEN
                CREATE POLICY profiles_read_own ON public.user_profiles FOR SELECT TO authenticated USING (auth_id = auth.uid());
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_profiles' AND policyname = 'profiles_update_own') THEN
                CREATE POLICY profiles_update_own ON public.user_profiles FOR UPDATE TO authenticated USING (auth_id = auth.uid()) WITH CHECK (auth_id = auth.uid());
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for table in (
        "user_actions",
        "reroute_jobs",
        "profile_locations",
        "profile_documents",
        "admin_profiles",
        "pantry_profiles",
        "store_profiles",
        "driver_profiles",
        "farmer_profiles",
        "user_profiles",
    ):
        op.execute(f"DROP TABLE IF EXISTS public.{table} CASCADE")
