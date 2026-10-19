"""异步数据库会话与连通性探测。"""
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def ping_db() -> bool:
    """数据库连通性探测，供健康检查使用。"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
