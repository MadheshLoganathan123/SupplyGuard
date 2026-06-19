import asyncio
from sqlalchemy import text
from app.database.session import engine


async def main():
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT 1"))
            print("DB connect OK:", r.scalar())
            tables = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
                )
            )
            print("Tables:", [t[0] for t in tables.fetchall()])
    except Exception as e:
        print("DB ERROR:", type(e).__name__, e)


if __name__ == "__main__":
    asyncio.run(main())
