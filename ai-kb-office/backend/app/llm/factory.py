"""Provider 工厂：按配置选择大模型实现。"""
from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.providers import OllamaProvider, OpenAICompatibleProvider


@lru_cache
def get_provider() -> LLMProvider:
    provider = get_settings().llm_provider.lower()
    if provider == "openai":
        return OpenAICompatibleProvider()
    return OllamaProvider()
