"""
大模型对话 API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, AsyncGenerator
import json
from pathlib import Path
from aiohttp import ClientTimeout

router = APIRouter(prefix="/llm", tags=["大模型"])

# 导入配置
CONFIG_FILE = Path(__file__).parent.parent.parent / "configs" / "settings.json"


def load_config() -> dict:
    """加载配置"""
    if not CONFIG_FILE.exists():
        return {
            "llm": {
                "provider": "ollama",
                "ollama": {"base_url": "http://localhost:11434", "model": "qwen2.5:7b"},
                "openai": {"api_key": "", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
                "deepseek": {"api_key": "", "base_url": "https://api.deepseek.com", "model": "deepseek-chat"}
            }
        }
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"llm": {"provider": "ollama"}}


class Message(BaseModel):
    role: str  # system, user, assistant
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = False


class ChatResponse(BaseModel):
    content: str
    model: str


async def stream_chat_response(config: dict, messages: List[Message]) -> AsyncGenerator[str, None]:
    """流式聊天响应"""
    from openai import AsyncOpenAI
    import sys
    
    client = AsyncOpenAI(
        api_key=config.get("api_key") or "no-key",
        base_url=config["base_url"]
    )
    
    try:
        async for chunk in await client.chat.completions.create(
            model=config.get("model", "default"),
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=4096,
            temperature=0.7,
            stream=True
        ):
            print(f"[DEBUG stream] chunk: {chunk}", file=sys.stderr)
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if not delta:
                continue
            if hasattr(delta, 'content') and delta.content:
                yield f"data: {json.dumps({'content': delta.content})}\n\n"
            elif hasattr(delta, 'reasoning') and delta.reasoning:
                yield f"data: {json.dumps({'content': delta.reasoning})}\n\n"
    except Exception as e:
        print(f"[ERROR stream] {e}", file=sys.stderr)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


async def call_ollama(config: dict, messages: List[Message]) -> str:
    """调用 Ollama"""
    import aiohttp
    
    url = f"{config['base_url']}/api/chat"
    payload = {
        "model": config["model"],
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream": False
    }
    
    timeout = ClientTimeout(total=120)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=timeout) as response:
            if response.status == 200:
                data = await response.json()
                return data["message"]["content"]
            else:
                raise HTTPException(status_code=500, detail=f"Ollama 调用失败：{response.status}")


async def call_openai(config: dict, messages: List[Message]) -> str:
    """调用 OpenAI"""
    import aiohttp
    
    if not config.get("api_key"):
        raise HTTPException(status_code=400, detail="API Key 未配置")
    
    url = f"{config['base_url']}/chat/completions"
    payload = {
        "model": config["model"],
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream": False
    }
    
    timeout = ClientTimeout(total=120)
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
        async with session.post(url, headers=headers, json=payload, timeout=timeout) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            elif response.status == 401:
                raise HTTPException(status_code=401, detail="API Key 无效")
            else:
                raise HTTPException(status_code=500, detail=f"OpenAI 调用失败：{response.status}")


async def call_deepseek(config: dict, messages: List[Message]) -> str:
    """调用 DeepSeek"""
    import aiohttp
    
    if not config.get("api_key"):
        raise HTTPException(status_code=400, detail="API Key 未配置")
    
    url = f"{config['base_url']}/chat/completions"
    payload = {
        "model": config["model"],
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream": False
    }
    
    timeout = ClientTimeout(total=120)
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
        async with session.post(url, headers=headers, json=payload, timeout=timeout) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            elif response.status == 401:
                raise HTTPException(status_code=401, detail="API Key 无效")
            else:
                raise HTTPException(status_code=500, detail=f"DeepSeek 调用失败：{response.status}")


async def call_custom(config: dict, messages: List[Message]) -> str:
    """调用自定义大模型"""
    from openai import AsyncOpenAI
    
    if not config.get("base_url"):
        raise HTTPException(status_code=400, detail="API 地址未配置")
    
    import sys
    print(f"[DEBUG call_custom] config: {config}", file=sys.stderr)
    print(f"[DEBUG call_custom] messages: {messages}", file=sys.stderr)
    
    try:
        # 使用 OpenAI 客户端
        client = AsyncOpenAI(
            api_key=config.get("api_key") or "no-key",
            base_url=config["base_url"]
        )
        
        print(f"[DEBUG call_custom] Creating chat completion with model: {config.get('model')}", file=sys.stderr)
        
        response = await client.chat.completions.create(
            model=config.get("model", "default"),
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=4096,
            temperature=0.7
        )
        
        print(f"[DEBUG call_custom] Response: {response}", file=sys.stderr)
        
        msg = response.choices[0].message
        # 处理 content 为 None 的情况，有些模型返回在 reasoning 字段
        content = msg.content or getattr(msg, 'reasoning', None) or ""
        print(f"[DEBUG call_custom] Final content: {content}", file=sys.stderr)
        return content
    
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR call_custom] Exception: {type(e).__name__} - {error_msg}", file=sys.stderr)
        if "401" in error_msg or "Authentication" in error_msg:
            raise HTTPException(status_code=401, detail="API Key 无效")
        raise HTTPException(status_code=500, detail=f"自定义大模型调用失败：{error_msg}")


@router.post("/chat")
async def chat(request: ChatRequest):
    """大模型对话"""
    config = load_config()
    provider = config["llm"]["provider"]
    
    # 调试日志
    import sys
    print(f"[DEBUG] Provider: {provider}", file=sys.stderr)
    print(f"[DEBUG] Config file: {CONFIG_FILE}", file=sys.stderr)
    print(f"[DEBUG] Config exists: {CONFIG_FILE.exists()}", file=sys.stderr)
    print(f"[DEBUG] Stream mode: {request.stream}", file=sys.stderr)
    
    # 流式响应
    if request.stream and provider == "custom":
        return StreamingResponse(
            stream_chat_response(config["llm"]["custom"], request.messages),
            media_type="text/event-stream"
        )
    
    try:
        if provider == "ollama":
            content = await call_ollama(config["llm"]["ollama"], request.messages)
        elif provider == "openai":
            content = await call_openai(config["llm"]["openai"], request.messages)
        elif provider == "deepseek":
            content = await call_deepseek(config["llm"]["deepseek"], request.messages)
        elif provider == "custom":
            content = await call_custom(config["llm"]["custom"], request.messages)
        else:
            raise HTTPException(status_code=400, detail="不支持的大模型提供商")
        
        return ChatResponse(content=content, model=config[f"llm"][provider].get("model", "unknown"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大模型调用失败：{str(e)}")
