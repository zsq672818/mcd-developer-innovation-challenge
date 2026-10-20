"""大模型连通性验证接口（任务 T0.6）：能成功调用一次本地或云端模型并返回结果。"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.llm.base import ChatMessage
from app.llm.factory import get_provider

router = APIRouter(prefix="/llm", tags=["llm"])


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    prompt: str | None = None


class ChatResponse(BaseModel):
    provider: str
    reply: str


@router.get("/health")
async def llm_health() -> dict:
    provider = get_provider()
    result = await provider.health()
    result["provider"] = provider.name
    return result


@router.post("/chat", response_model=ChatResponse)
async def llm_chat(req: ChatRequest) -> ChatResponse:
    provider = get_provider()
    messages = list(req.messages)
    if req.prompt:
        messages.append({"role": "user", "content": req.prompt})
    if not messages:
        messages = [{"role": "user", "content": "你好，请用一句话自我介绍。"}]
    reply = await provider.chat(messages)
    return ChatResponse(provider=provider.name, reply=reply)
