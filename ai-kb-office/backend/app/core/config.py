"""应用配置：全部通过环境变量注入，禁止写死在代码里（见计划 7.2 节）。"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 应用
    app_name: str = "AI 知识库办公平台"
    app_env: str = "dev"
    debug: bool = True
    api_prefix: str = "/api"

    # 数据库
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_kb"

    # 大模型
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = "http://localhost:11434"
    llm_api_key: str = ""
    llm_timeout: int = 60

    # 存储
    storage_dir: str = "./storage"

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
