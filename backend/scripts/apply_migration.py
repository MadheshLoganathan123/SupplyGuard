"""Apply dashboard/logistics SQL migrations to Supabase Postgres."""

import asyncio

from sqlalchemy import text

from app.database.session import engine

STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS public.incidents (
        id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
        title           VARCHAR(255) NOT NULL,
        description     TEXT,
        sector          VARCHAR(50),
        severity        VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
        status          VARCHAR(20) NOT NULL DEFAULT 'OPEN',
        occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        resolved_at     TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS public.telemetry (
        id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
        node_id         UUID,
        shipment_id     UUID        REFERENCES public.shipments(id) ON DELETE SET NULL,
        type            VARCHAR(50) NOT NULL,
        payload         JSONB       NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS public.interventions (
        id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id         UUID,
        text            TEXT        NOT NULL,
        status          VARCHAR(20) NOT NULL DEFAULT 'queued',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    INSERT INTO public.agents (name, agent_type, status, sector, efficiency_score)
    VALUES ('Gig-D22', 'LOGISTICS', 'ACTIVE', 'Sector 7', 92.5)
    ON CONFLICT (name) DO NOTHING
    """,
    """
    INSERT INTO public.agents (name, agent_type, status, sector, efficiency_score)
    VALUES ('Truck-A14', 'LOGISTICS', 'ACTIVE', 'Sector 12', 88.0)
    ON CONFLICT (name) DO NOTHING
    """,
]


async def main() -> None:
    async with engine.begin() as conn:
        for stmt in STATEMENTS:
            await conn.execute(text(stmt))
    print("Migration applied successfully.")


if __name__ == "__main__":
    asyncio.run(main())
