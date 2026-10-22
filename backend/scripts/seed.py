import asyncio

from app.db.session import AsyncSessionLocal


async def seed_data() -> None:
    """Entrypoint for seeding initial development data."""
    async with AsyncSessionLocal() as _session:
        print("Seeding initial database records...")
        # Add initial seed logic here


if __name__ == "__main__":
    asyncio.run(seed_data())
