-- Network topology + Reports feature tables
-- Run in Supabase SQL editor or via scripts/apply_network_reports_migration.py

CREATE TABLE IF NOT EXISTS public.supply_nodes (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL UNIQUE,
    node_type           VARCHAR(50)  NOT NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT 'OPERATIONAL',
    agent_name          VARCHAR(100),
    image_url           VARCHAR(500),
    inventory_level     NUMERIC(5,2),
    inventory_label     VARCHAR(100),
    threat_level        VARCHAR(100),
    throughput          VARCHAR(50),
    sector              VARCHAR(50),
    position_index      INT          NOT NULL DEFAULT 0,
    connections         JSONB        NOT NULL DEFAULT '[]',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.projections (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    type            VARCHAR(50) NOT NULL DEFAULT 'demand',
    input           JSONB       NOT NULL DEFAULT '{}',
    result          JSONB,
    status          VARCHAR(20) NOT NULL DEFAULT 'queued',
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.heuristics (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    payload         JSONB       NOT NULL DEFAULT '{}',
    version         INT         NOT NULL DEFAULT 1,
    created_by      UUID,
    active          BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.agent_performance (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id        UUID        REFERENCES public.agents(id) ON DELETE CASCADE,
    metrics         JSONB       NOT NULL DEFAULT '{}',
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.export_jobs (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    format          VARCHAR(10) NOT NULL,
    query           JSONB       NOT NULL DEFAULT '{}',
    status          VARCHAR(20) NOT NULL DEFAULT 'queued',
    result_data     JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

-- Seed topology nodes matching the Network UI
INSERT INTO public.supply_nodes (name, node_type, status, agent_name, image_url, inventory_level, inventory_label, threat_level, throughput, sector, position_index, connections)
VALUES
(
    'Farm #204', 'FARM', 'OPERATIONAL', 'Sourcing Agent: Alpha-9',
    '/images/vertical_farm.jpg', 82.0, '82% (High)', 'Low (Minor Delay)', '1.2k units/hr', 'Sector 3', 0,
    '[{"name":"Drone Fleet Beta","type":"drone","status":"active","eta":"12 mins"},{"name":"Aerial Transport 04","type":"flight","status":"pending","eta":"Loading"}]'::jsonb
),
(
    'Warehouse B', 'WAREHOUSE', 'OPERATIONAL', 'Sourcing Agent: Omega-4',
    '/images/earth_network.jpg', 94.0, '94% (Full)', 'None', '4.8k units/hr', 'Sector 5', 1,
    '[{"name":"Truck Convoy Sector 7","type":"truck","status":"active","eta":"45 mins"},{"name":"Drone Fleet Alpha","type":"drone","status":"active","eta":"5 mins"}]'::jsonb
),
(
    'Retail Store Delta', 'RETAIL', 'AT_RISK', 'Recipient Agent: Delta-3',
    '/images/map_logistics.jpg', 21.0, '21% (Critical Low)', 'High (Sector 7 Flood)', '450 units/hr', 'Sector 7', 2,
    '[{"name":"Emergency Courier 9","type":"drone","status":"pending","eta":"Delayed"}]'::jsonb
),
(
    'Shipping Node 71', 'SHIPPING', 'BLOCKED', 'Logistics Agent: Sigma-12',
    '/images/map_command_center.jpg', 55.0, '55% (Static)', 'Critical (Road Closed)', '0 units/hr', 'Sector 12', 3,
    '[]'::jsonb
)
ON CONFLICT (name) DO NOTHING;

-- Seed filler nodes for topology counts (operational/at-risk/blocked distribution)
INSERT INTO public.supply_nodes (name, node_type, status, agent_name, inventory_level, inventory_label, threat_level, throughput, position_index)
SELECT
    'Node-' || gs,
    CASE (gs % 4) WHEN 0 THEN 'FARM' WHEN 1 THEN 'WAREHOUSE' WHEN 2 THEN 'RETAIL' ELSE 'SHIPPING' END,
    CASE
        WHEN gs <= 138 THEN 'OPERATIONAL'
        WHEN gs <= 152 THEN 'AT_RISK'
        ELSE 'BLOCKED'
    END,
    'Auto Agent ' || gs,
    50 + (gs % 50),
    (50 + (gs % 50))::text || '%',
    'Low',
    (gs % 10 + 1)::text || '00 units/hr',
    gs + 3
FROM generate_series(1, 155) AS gs
ON CONFLICT (name) DO NOTHING;

-- Seed agents for Reports performance panel
INSERT INTO public.agents (name, agent_type, status, sector, efficiency_score)
VALUES
    ('Optimax-9 Core', 'CORE_AI', 'ACTIVE', 'Global', 98.4),
    ('Vanguard-Beta', 'CORE_AI', 'ACTIVE', 'Sector 7', 91.2),
    ('Sentinel-Shield', 'CORE_AI', 'ACTIVE', 'Sector 12', 94.7)
ON CONFLICT (name) DO NOTHING;

-- Seed agent performance snapshots
INSERT INTO public.agent_performance (agent_id, metrics)
SELECT a.id, jsonb_build_object(
    'efficiency_pct', a.efficiency_score,
    'negotiation_speed_avg_sec', CASE a.name WHEN 'Optimax-9 Core' THEN 1.2 WHEN 'Vanguard-Beta' THEN 0.8 ELSE 2.4 END,
    'route_accuracy_pct', CASE a.name WHEN 'Optimax-9 Core' THEN 99.1 WHEN 'Vanguard-Beta' THEN 88.5 ELSE 95.4 END,
    'badge', CASE a.name WHEN 'Optimax-9 Core' THEN 'Top Performer' WHEN 'Vanguard-Beta' THEN 'Experimental' ELSE 'Stable' END
)
FROM public.agents a
WHERE a.name IN ('Optimax-9 Core', 'Vanguard-Beta', 'Sentinel-Shield', 'Gig-D22', 'Truck-A14')
AND NOT EXISTS (
    SELECT 1 FROM public.agent_performance ap WHERE ap.agent_id = a.id
);

-- Default heuristics calibration
INSERT INTO public.heuristics (name, payload, version, active)
SELECT 'default_calibration', '{"negotiation_speed_bias": 60, "route_accuracy_bias": 80}'::jsonb, 1, TRUE
WHERE NOT EXISTS (SELECT 1 FROM public.heuristics WHERE name = 'default_calibration');

-- Sample incidents for Reports historical panel
INSERT INTO public.incidents (title, description, sector, severity, status, occurred_at, resolved_at)
SELECT * FROM (VALUES
    (
        'Sector 7 Flash Flood - Resolved',
        'AI Agent detected rising water levels 4 hours before crest. Automated rerouting of 14 grain convoys saved $2.1M in spoilage.',
        'Sector 7', 'HIGH', 'RESOLVED', NOW() - INTERVAL '30 days', NOW() - INTERVAL '28 days'
    ),
    (
        'Local Labor Strike - Mitigated',
        'Negotiation agent initiated fair-market rate adjustments for carrier sub-contractors, avoiding a 48-hour port shutdown.',
        'Sector 4', 'MEDIUM', 'RESOLVED', NOW() - INTERVAL '45 days', NOW() - INTERVAL '43 days'
    ),
    (
        'Border Congestion Peak',
        'Dynamic multi-point routing bypassed Grade A checkpoint, reducing border dwell time by 12% across 400+ shipments.',
        'Sector 12', 'LOW', 'RESOLVED', NOW() - INTERVAL '60 days', NOW() - INTERVAL '58 days'
    )
) AS v(title, description, sector, severity, status, occurred_at, resolved_at)
WHERE NOT EXISTS (SELECT 1 FROM public.incidents LIMIT 1);
