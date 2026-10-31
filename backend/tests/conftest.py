import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import AsyncSessionLocal, engine
from app.main import app
from app.middleware.RateLimiterMiddleware import rate_limiter_instance


@pytest.fixture(autouse=True)
async def cleanup_db_engine():
    rate_limiter_instance.reset()
    yield
    rate_limiter_instance.reset()
    try:
        # Drain pending async fire-and-forget background tasks before pool disposal
        await asyncio.sleep(0.05)
        await engine.dispose()
    except (OSError, Exception):
        pass


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession for direct DB state assertions in tests."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        try:
            await session.rollback()
        except Exception:
            pass
        try:
            await session.close()
        except Exception:
            pass
