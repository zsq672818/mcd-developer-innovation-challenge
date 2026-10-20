"""健康检查接口（任务 T0.3；G0 准出条件含健康检查通过）。"""
from fastapi import APIRouter

from app.core.config import get_settings
from app.db.session import ping_db

router = APIRouter(tags=["health"])
_settings = get_settings()


@router.get("/health")
async def health() -> dict:
    """存活探针：进程可用即返回 ok。"""
    return {"status": "ok", "app": _settings.app_name, "env": _settings.app_env}


@router.get("/health/ready")
async def readiness() -> dict:
    """就绪探针：附加数据库连通性。"""
    db_ok = await ping_db()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down",
        "database_url_scheme": _settings.database_url.split("://", 1)[0],
    }
