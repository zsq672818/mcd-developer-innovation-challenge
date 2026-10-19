"""大模型 Provider 抽象层雏形（任务 T0.6）。"""
from abc import ABC, abstractmethod
from typing import TypedDict


class ChatMessage(TypedDict):
    role: str  # system | user | assistant
    content: str


class LLMProvider(ABC):
    """统一的大模型调用接口。本地 Ollama 与云端 OpenAI 兼容 API 均按此实现。"""

    name: str = "base"

    @abstractmethod
    async def chat(self, messages: list[ChatMessage]) -> str:
        """发送对话消息，返回模型回答文本。"""
        raise NotImplementedError

    @abstractmethod
    async def health(self) -> dict:
        """探测模型服务连通性，返回 {ok, detail}。"""
        raise NotImplementedError
