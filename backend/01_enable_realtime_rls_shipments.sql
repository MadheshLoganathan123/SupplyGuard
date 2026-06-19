-- Create agents table
CREATE TABLE IF NOT EXISTS public.agents (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    agent_type      VARCHAR(50) NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'IDLE',
    sector          VARCHAR(50),
    efficiency_score NUMERIC(5,2) DEFAULT 0.0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create shipments table
CREATE TABLE IF NOT EXISTS public.shipments (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    shipment_code   VARCHAR(20) NOT NULL UNIQUE,
    origin          VARCHAR(255) NOT NULL,
    destination     VARCHAR(255) NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'IN-TRANSIT',
    agent_id        UUID        REFERENCES public.agents(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS on shipments
ALTER TABLE public.shipments ENABLE ROW LEVEL SECURITY;

-- Create policies for shipments
CREATE POLICY "Allow authenticated read" ON public.shipments FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated insert" ON public.shipments FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated update" ON public.shipments FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow authenticated delete" ON public.shipments FOR DELETE TO authenticated USING (true);

-- Enable realtime for shipments
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND tablename = 'shipments'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.shipments;
    END IF;
END $$;
