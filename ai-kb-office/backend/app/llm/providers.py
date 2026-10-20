"""大模型 Provider 实现：本地 Ollama 与云端 OpenAI 兼容 API。"""
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.base import ChatMessage, LLMProvider

logger = get_logger(__name__)
_settings = get_settings()


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.base_url = _settings.llm_base_url.rstrip("/")
        self.model = _settings.llm_model

    async def chat(self, messages: list[ChatMessage]) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": False}
        async with httpx.AsyncClient(timeout=_settings.llm_timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("message", {}).get("content", "")

    async def health(self) -> dict:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            models = [m.get("name") for m in resp.json().get("models", [])]
            return {"ok": True, "detail": f"Ollama 可达，已加载模型：{models}"}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama 健康检查失败: %s", exc)
            return {"ok": False, "detail": f"Ollama 不可达：{exc}"}


class OpenAICompatibleProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        self.base_url = _settings.llm_base_url.rstrip("/")
        self.model = _settings.llm_model
        self.api_key = _settings.llm_api_key

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat(self, messages: list[ChatMessage]) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {"model": self.model, "messages": messages, "stream": False}
        async with httpx.AsyncClient(timeout=_settings.llm_timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def health(self) -> dict:
        url = f"{self.base_url}/v1/models"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
            return {"ok": True, "detail": "云端模型服务可达"}
        except Exception as exc:  # noqa: BLE001
            logger.warning("云端模型健康检查失败: %s", exc)
            return {"ok": False, "detail": f"云端模型不可达：{exc}"}
