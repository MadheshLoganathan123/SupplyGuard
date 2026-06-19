"""Apply network + reports SQL migrations to Supabase Postgres."""

import asyncio
from pathlib import Path

from sqlalchemy import text

from app.database.session import engine

SQL_PATH = Path(__file__).resolve().parent.parent / "03_network_reports_tables.sql"


async def main() -> None:
    sql = SQL_PATH.read_text(encoding="utf-8")
    # Strip line comments so chunks starting with headers are not skipped
    lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    cleaned = "\n".join(lines)
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]

    async with engine.begin() as conn:
        for stmt in statements:
            await conn.execute(text(stmt))
    print("Network + reports migration applied successfully.")


if __name__ == "__main__":
    asyncio.run(main())
