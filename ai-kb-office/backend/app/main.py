"""FastAPI 应用入口（任务 T0.3）。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, llm
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging

_settings = get_settings()
setup_logging(_settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("启动 %s（env=%s）", _settings.app_name, _settings.app_env)
    logger.info("数据库：%s", _settings.database_url.split("://", 1)[0])
    logger.info("大模型：provider=%s model=%s", _settings.llm_provider, _settings.llm_model)
    yield
    logger.info("应用关闭")


app = FastAPI(
    title=_settings.app_name,
    version="0.1.0",
    description="基于数据库与知识库的 AI 办公平台",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=_settings.api_prefix)
app.include_router(llm.router, prefix=_settings.api_prefix)


@app.get("/")
async def root() -> dict:
    return {"name": _settings.app_name, "docs": "/docs", "api": _settings.api_prefix}
