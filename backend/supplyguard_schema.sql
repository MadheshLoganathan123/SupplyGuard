-- ============================================================
--  SupplyGuard — Full Database Schema
--  Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- 1. USERS
--    Core identity table — links to Supabase Auth (auth.users)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.users (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id         UUID        UNIQUE,                         -- references auth.users.id
    full_name       TEXT        NOT NULL,
    email           TEXT        NOT NULL UNIQUE,
    phone           TEXT,
    role            TEXT        NOT NULL DEFAULT 'viewer'
                                CHECK (role IN ('admin','operator','farmer','driver','store_manager','viewer')),
    avatar_url      TEXT,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.users          IS 'Platform users linked to Supabase Auth.';
COMMENT ON COLUMN public.users.auth_id  IS 'References auth.users.id from Supabase Auth.';
COMMENT ON COLUMN public.users.role     IS 'admin | operator | farmer | driver | store_manager | viewer';


-- ============================================================
-- 2. FARMERS
--    Agricultural supply-side nodes (farms, greenhouses, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.farmers (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID        REFERENCES public.users(id) ON DELETE SET NULL,
    farm_name       TEXT        NOT NULL,
    farm_type       TEXT        NOT NULL DEFAULT 'conventional'
                                CHECK (farm_type IN ('conventional','vertical','greenhouse','hydroponic','organic')),
    sector          TEXT,                                       -- e.g. "Sector 7"
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),
    total_area_sqm  NUMERIC(12,2),
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    agent_code      TEXT,                                       -- assigned AI agent identifier
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.farmers IS 'Supply-side agricultural nodes managed by the platform.';


-- ============================================================
-- 3. DRIVERS
--    Last-mile and mid-mile delivery agents
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drivers (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID        REFERENCES public.users(id) ON DELETE SET NULL,
    vehicle_type    TEXT        NOT NULL DEFAULT 'motorcycle'
                                CHECK (vehicle_type IN ('motorcycle','cargo_bike','van','truck','drone','aerial')),
    vehicle_plate   TEXT,
    capacity_kg     NUMERIC(8,2),
    sector          TEXT,
    status          TEXT        NOT NULL DEFAULT 'idle'
                                CHECK (status IN ('idle','active','en_route','offline')),
    current_lat     NUMERIC(9,6),
    current_lng     NUMERIC(9,6),
    utilization_pct NUMERIC(5,2) DEFAULT 0.0
                                CHECK (utilization_pct BETWEEN 0 AND 100),
    agent_code      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.drivers IS 'Delivery drivers and autonomous units in the logistics fleet.';


-- ============================================================
-- 4. STORES
--    Retail and wholesale distribution nodes
-- ============================================================
CREATE TABLE IF NOT EXISTS public.stores (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    manager_id      UUID        REFERENCES public.users(id) ON DELETE SET NULL,
    store_name      TEXT        NOT NULL,
    store_type      TEXT        NOT NULL DEFAULT 'retail'
                                CHECK (store_type IN ('retail','wholesale','cooperative','emergency_hub')),
    sector          TEXT,
    address         TEXT,
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.stores IS 'Retail and wholesale distribution points.';


-- ============================================================
-- 5. PANTRIES
--    Community food pantries and emergency food access points
-- ============================================================
CREATE TABLE IF NOT EXISTS public.pantries (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    coordinator_id  UUID        REFERENCES public.users(id) ON DELETE SET NULL,
    pantry_name     TEXT        NOT NULL,
    sector          TEXT,
    address         TEXT,
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),
    capacity_units  INTEGER,                                    -- max stock units
    current_units   INTEGER     NOT NULL DEFAULT 0,
    status          TEXT        NOT NULL DEFAULT 'operational'
                                CHECK (status IN ('operational','at_risk','critical','closed')),
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.pantries IS 'Community food access points and emergency pantries.';


-- ============================================================
-- 6. INVENTORY
--    Stock levels at farms, stores, and pantries
-- ============================================================
CREATE TABLE IF NOT EXISTS public.inventory (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- polymorphic owner: one of these must be set
    farmer_id       UUID        REFERENCES public.farmers(id)  ON DELETE CASCADE,
    store_id        UUID        REFERENCES public.stores(id)   ON DELETE CASCADE,
    pantry_id       UUID        REFERENCES public.pantries(id) ON DELETE CASCADE,

    item_name       TEXT        NOT NULL,
    category        TEXT        NOT NULL DEFAULT 'general'
                                CHECK (category IN ('grain','produce','dairy','protein','medical','water','general')),
    quantity        NUMERIC(12,2) NOT NULL DEFAULT 0,
    unit            TEXT        NOT NULL DEFAULT 'kg'
                                CHECK (unit IN ('kg','litre','units','tonnes','boxes')),
    min_threshold   NUMERIC(12,2) NOT NULL DEFAULT 0,          -- alert below this
    max_capacity    NUMERIC(12,2),
    expiry_date     DATE,
    last_updated_by UUID        REFERENCES public.users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT inventory_owner_check CHECK (
        (farmer_id IS NOT NULL)::INT +
        (store_id  IS NOT NULL)::INT +
        (pantry_id IS NOT NULL)::INT = 1
    )
);

COMMENT ON TABLE  public.inventory                   IS 'Stock levels across all supply nodes.';
COMMENT ON COLUMN public.inventory.min_threshold     IS 'System triggers an alert when quantity drops below this value.';


-- ============================================================
-- 7. THREATS
--    Active supply chain disruptions (floods, strikes, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.threats (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT        NOT NULL,
    description     TEXT,
    threat_type     TEXT        NOT NULL DEFAULT 'environmental'
                                CHECK (threat_type IN (
                                    'environmental','conflict','infrastructure',
                                    'economic','health','logistics','other'
                                )),
    severity        TEXT        NOT NULL DEFAULT 'medium'
                                CHECK (severity IN ('low','medium','high','critical')),
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','monitoring','mitigated','resolved')),
    affected_sector TEXT,
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),
    radius_km       NUMERIC(6,2),                              -- affected radius
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ,
    reported_by     UUID        REFERENCES public.users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.threats IS 'Active and historical supply chain disruption events.';


-- ============================================================
-- 8. ROUTES
--    AI-computed delivery paths between supply nodes
-- ============================================================
CREATE TABLE IF NOT EXISTS public.routes (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_code      TEXT        NOT NULL UNIQUE,               -- e.g. "PATH-A-EXPRESS"
    origin_label    TEXT        NOT NULL,
    destination_label TEXT      NOT NULL,
    origin_lat      NUMERIC(9,6),
    origin_lng      NUMERIC(9,6),
    dest_lat        NUMERIC(9,6),
    dest_lng        NUMERIC(9,6),
    distance_km     NUMERIC(8,2),
    estimated_mins  INTEGER,
    route_type      TEXT        NOT NULL DEFAULT 'standard'
                                CHECK (route_type IN ('standard','express','secure','emergency','bypass')),
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','blocked','degraded','inactive')),
    threat_id       UUID        REFERENCES public.threats(id) ON DELETE SET NULL,  -- blocking threat if any
    efficiency_pct  NUMERIC(5,2) DEFAULT 100.0
                                CHECK (efficiency_pct BETWEEN 0 AND 100),
    computed_by     TEXT,                                      -- agent name that computed this route
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.routes IS 'AI-optimised delivery routes between supply nodes.';


-- ============================================================
-- 9. DELIVERIES
--    Individual shipment records linking drivers to routes
-- ============================================================
CREATE TABLE IF NOT EXISTS public.deliveries (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    shipment_code   TEXT        NOT NULL UNIQUE,               -- e.g. "#SS-4921"
    driver_id       UUID        REFERENCES public.drivers(id)  ON DELETE SET NULL,
    route_id        UUID        REFERENCES public.routes(id)   ON DELETE SET NULL,
    farmer_id       UUID        REFERENCES public.farmers(id)  ON DELETE SET NULL,   -- origin node
    store_id        UUID        REFERENCES public.stores(id)   ON DELETE SET NULL,   -- destination (store)
    pantry_id       UUID        REFERENCES public.pantries(id) ON DELETE SET NULL,   -- destination (pantry)
    status          TEXT        NOT NULL DEFAULT 'pending'
                                CHECK (status IN (
                                    'pending','in_transit','rerouted',
                                    'perimeter_drop','delivered','delayed','cancelled'
                                )),
    priority        TEXT        NOT NULL DEFAULT 'normal'
                                CHECK (priority IN ('low','normal','high','emergency')),
    payload_kg      NUMERIC(8,2),
    notes           TEXT,
    dispatched_at   TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.deliveries IS 'Individual shipment records tracking goods from source to destination.';


-- ============================================================
-- 10. AGENT_LOGS
--     Immutable audit trail of every AI agent action
-- ============================================================
CREATE TABLE IF NOT EXISTS public.agent_logs (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name      TEXT        NOT NULL,                      -- e.g. "Logistics Agent"
    agent_type      TEXT        NOT NULL DEFAULT 'logistics'
                                CHECK (agent_type IN ('logistics','sourcing','recipient','core_ai')),
    action_type     TEXT        NOT NULL,                      -- e.g. "REROUTE", "ALLOCATE_SURPLUS"
    -- optional FK references to affected entities
    delivery_id     UUID        REFERENCES public.deliveries(id) ON DELETE SET NULL,
    threat_id       UUID        REFERENCES public.threats(id)   ON DELETE SET NULL,
    route_id        UUID        REFERENCES public.routes(id)    ON DELETE SET NULL,
    farmer_id       UUID        REFERENCES public.farmers(id)   ON DELETE SET NULL,

    payload         JSONB,                                     -- full action context/parameters
    result          JSONB,                                     -- outcome returned by the agent
    confidence      NUMERIC(4,3) CHECK (confidence BETWEEN 0 AND 1),
    status          TEXT        NOT NULL DEFAULT 'success'
                                CHECK (status IN ('success','failed','partial','pending')),
    message         TEXT,                                      -- human-readable summary
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.agent_logs             IS 'Immutable audit log of all AI agent actions.';
COMMENT ON COLUMN public.agent_logs.payload     IS 'Input context passed to the agent (JSONB).';
COMMENT ON COLUMN public.agent_logs.result      IS 'Output/decision returned by the agent (JSONB).';
COMMENT ON COLUMN public.agent_logs.confidence  IS 'Agent confidence score between 0.000 and 1.000.';


-- ============================================================
-- INDEXES — common query patterns
-- ============================================================

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email    ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_auth_id  ON public.users(auth_id);
CREATE INDEX IF NOT EXISTS idx_users_role     ON public.users(role);

-- Farmers
CREATE INDEX IF NOT EXISTS idx_farmers_sector     ON public.farmers(sector);
CREATE INDEX IF NOT EXISTS idx_farmers_user_id    ON public.farmers(user_id);

-- Drivers
CREATE INDEX IF NOT EXISTS idx_drivers_status     ON public.drivers(status);
CREATE INDEX IF NOT EXISTS idx_drivers_sector     ON public.drivers(sector);

-- Stores / Pantries
CREATE INDEX IF NOT EXISTS idx_stores_sector      ON public.stores(sector);
CREATE INDEX IF NOT EXISTS idx_pantries_status    ON public.pantries(status);
CREATE INDEX IF NOT EXISTS idx_pantries_sector    ON public.pantries(sector);

-- Inventory
CREATE INDEX IF NOT EXISTS idx_inventory_farmer   ON public.inventory(farmer_id);
CREATE INDEX IF NOT EXISTS idx_inventory_store    ON public.inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_inventory_pantry   ON public.inventory(pantry_id);
CREATE INDEX IF NOT EXISTS idx_inventory_category ON public.inventory(category);

-- Threats
CREATE INDEX IF NOT EXISTS idx_threats_status     ON public.threats(status);
CREATE INDEX IF NOT EXISTS idx_threats_severity   ON public.threats(severity);
CREATE INDEX IF NOT EXISTS idx_threats_sector     ON public.threats(affected_sector);

-- Routes
CREATE INDEX IF NOT EXISTS idx_routes_status      ON public.routes(status);
CREATE INDEX IF NOT EXISTS idx_routes_type        ON public.routes(route_type);

-- Deliveries
CREATE INDEX IF NOT EXISTS idx_deliveries_status      ON public.deliveries(status);
CREATE INDEX IF NOT EXISTS idx_deliveries_driver      ON public.deliveries(driver_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_route       ON public.deliveries(route_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_dispatched  ON public.deliveries(dispatched_at DESC);

-- Agent Logs
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_name  ON public.agent_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_logs_action_type ON public.agent_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_agent_logs_executed_at ON public.agent_logs(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_delivery    ON public.agent_logs(delivery_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_threat      ON public.agent_logs(threat_id);


-- ============================================================
-- AUTO-UPDATE updated_at TRIGGER
-- ============================================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables that have updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'users','farmers','drivers','stores','pantries',
        'inventory','threats','routes','deliveries'
    ]
    LOOP
        EXECUTE format(
            'CREATE OR REPLACE TRIGGER trg_%s_updated_at
             BEFORE UPDATE ON public.%s
             FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();',
            t, t
        );
    END LOOP;
END;
$$;


-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable RLS — add your own policies as needed
-- ============================================================
ALTER TABLE public.users        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farmers      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.drivers      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stores       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pantries     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.threats      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.routes       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deliveries   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_logs   ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all public operational data
CREATE POLICY "authenticated_read_all" ON public.farmers
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.drivers
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.stores
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.pantries
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.inventory
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.threats
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.routes
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.deliveries
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_all" ON public.agent_logs
    FOR SELECT TO authenticated USING (true);

-- Users can read/update their own profile
CREATE POLICY "users_read_own" ON public.users
    FOR SELECT TO authenticated USING (auth_id = auth.uid());

CREATE POLICY "users_update_own" ON public.users
    FOR UPDATE TO authenticated USING (auth_id = auth.uid());


-- ============================================================
-- SEED — minimal reference data for testing
-- ============================================================
INSERT INTO public.routes (route_code, origin_label, destination_label, distance_km, route_type, efficiency_pct, computed_by)
VALUES
    ('PATH-A-EXPRESS', 'Valley Farms Hub',   'Midtown Pantry',       8.2,  'express',   85.0, 'Logistics Agent'),
    ('PATH-B-SECURE',  'Central Wholesale',  'Independent Grocer 4', 12.4, 'secure',    98.0, 'Logistics Agent'),
    ('PATH-C-BYPASS',  'Vertical Fields G3', 'Perimeter Drop-A',     6.7,  'bypass',    91.0, 'Core AI')
ON CONFLICT (route_code) DO NOTHING;
