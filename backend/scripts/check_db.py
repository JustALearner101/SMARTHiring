import asyncio

from sqlalchemy import text

from app.db.session import engine


async def check_database() -> None:
    """Verify PostgreSQL connectivity and pgvector extension availability."""
    async with engine.connect() as conn:
        version = (await conn.execute(text("SELECT version();"))).scalar_one()
        ext = (
            await conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            )
        ).scalar_one_or_none()
        print(f"Database connected: {version}")
        print(f"pgvector extension installed: {bool(ext)}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database())
