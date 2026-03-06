import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from landscraper.models import Base

TEST_DATABASE_URL = (
    "postgresql+asyncpg://landscraper:landscraper@localhost:5432/landscraper_test"
)
ADMIN_DATABASE_URL = (
    "postgresql+asyncpg://landscraper:landscraper@localhost:5432/landscraper"
)


@pytest.fixture(autouse=True, scope="session")
def disable_langsmith_tracing():
    """Ensure LangSmith tracing is disabled during tests."""
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)
    os.environ.pop("LANGCHAIN_PROJECT", None)
    yield


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    try:
        admin_engine = create_async_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
        async with admin_engine.connect() as conn:
            await conn.execute(text("DROP DATABASE IF EXISTS landscraper_test"))
            await conn.execute(text("CREATE DATABASE landscraper_test"))
        await admin_engine.dispose()
    except OSError:
        yield
        return

    test_engine = create_async_engine(TEST_DATABASE_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await test_engine.dispose()

    yield

    admin_engine = create_async_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS landscraper_test"))
    await admin_engine.dispose()


@pytest.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
    await engine.dispose()
