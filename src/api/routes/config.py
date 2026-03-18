"""
配置管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import json
from pathlib import Path
from aiohttp import ClientTimeout

router = APIRouter(prefix="/config", tags=["配置"])

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent.parent / "configs" / "settings.json"

# 默认配置
DEFAULT_CONFIG = {
    "llm": {
        "provider": "ollama",
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "qwen2.5:7b"
        },
        "openai": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        },
        "deepseek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "custom": {
            "name": "",
            "api_key": "",
            "base_url": "",
            "model": "",
            "chat_path": "/chat/completions"
        }
    },
    "data": {
        "update_time": "22:00",
        "history_days": 365
    }
}


class LLMConfig(BaseModel):
    provider: str
    ollama: dict = Field(default_factory=lambda: DEFAULT_CONFIG["llm"]["ollama"])
    openai: dict = Field(default_factory=lambda: DEFAULT_CONFIG["llm"]["openai"])
    deepseek: dict = Field(default_factory=lambda: DEFAULT_CONFIG["llm"]["deepseek"])
    custom: dict = Field(default_factory=lambda: DEFAULT_CONFIG["llm"]["custom"])


class DataConfig(BaseModel):
    update_time: str = Field(default="22:00")
    history_days: int = Field(default=365)


class ConfigSchema(BaseModel):
    llm: LLMConfig
    data: DataConfig


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG


def save_config(config: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


@router.get("/")
async def get_config():
    return load_config()


@router.put("/")
async def update_config(config: ConfigSchema):
    config_dict = config.model_dump()
    save_config(config_dict)
    return {"message": "配置已更新", "config": config_dict}


@router.post("/test-connection")
async def test_llm_connection(config: ConfigSchema):
    provider = config.llm.provider
    
    try:
        if provider == "ollama":
            return await test_ollama(config.llm.ollama)
        elif provider == "openai":
            return await test_openai(config.llm.openai)
        elif provider == "deepseek":
            return await test_deepseek(config.llm.deepseek)
        elif provider == "custom":
            return await test_custom(config.llm.custom)
        else:
            return {"success": False, "message": "不支持的大模型提供商"}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def test_ollama(ollama_config: dict) -> dict:
    import aiohttp
    
    url = f"{ollama_config['base_url']}/api/version"
    timeout = ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "message": f"Ollama 连接成功，版本：{data.get('version', 'unknown')}",
                        "model": ollama_config["model"]
                    }
                else:
                    return {"success": False, "message": f"Ollama 连接失败：{response.status}"}
    except aiohttp.ClientError as e:
        return {"success": False, "message": f"无法连接到 Ollama: {str(e)}"}


async def test_openai(openai_config: dict) -> dict:
    import aiohttp
    
    if not openai_config.get("api_key"):
        return {"success": False, "message": "API Key 未配置"}
    
    url = f"{openai_config['base_url']}/models"
    timeout = ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {openai_config['api_key']}"}
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "message": "OpenAI API 连接成功",
                        "model": openai_config["model"]
                    }
                elif response.status == 401:
                    return {"success": False, "message": "API Key 无效"}
                else:
                    return {"success": False, "message": f"OpenAI 连接失败：{response.status}"}
    except aiohttp.ClientError as e:
        return {"success": False, "message": f"无法连接到 OpenAI: {str(e)}"}


async def test_deepseek(deepseek_config: dict) -> dict:
    import aiohttp
    
    if not deepseek_config.get("api_key"):
        return {"success": False, "message": "API Key 未配置"}
    
    url = f"{deepseek_config['base_url']}/models"
    timeout = ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {deepseek_config['api_key']}"}
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "message": "DeepSeek API 连接成功",
                        "model": deepseek_config["model"]
                    }
                elif response.status == 401:
                    return {"success": False, "message": "API Key 无效"}
                else:
                    return {"success": False, "message": f"DeepSeek 连接失败：{response.status}"}
    except aiohttp.ClientError as e:
        return {"success": False, "message": f"无法连接到 DeepSeek: {str(e)}"}


async def test_custom(custom_config: dict) -> dict:
    """测试自定义大模型连接"""
    from openai import AsyncOpenAI
    
    if not custom_config.get("base_url"):
        return {"success": False, "message": "API 地址未配置"}
    
    config_model = custom_config.get("model", "")
    if not config_model:
        return {"success": False, "message": "模型名称未配置"}
    
    try:
        # 使用 OpenAI 客户端连接
        client = AsyncOpenAI(
            api_key=custom_config.get("api_key") or "no-key",
            base_url=custom_config["base_url"]
        )
        
        # 直接调用聊天接口测试
        response = await client.chat.completions.create(
            model=config_model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        
        msg = response.choices[0].message
        # 处理 content 为 None 的情况，有些模型返回在 reasoning 字段
        content = msg.content or getattr(msg, 'reasoning', None) or ""
        return {
            "success": True,
            "message": f"连接成功，模型回复：{content[:50]}",
            "model": config_model
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[DEBUG] test_custom error: {type(e).__name__} - {error_msg}")
        if "401" in error_msg or "Authentication" in error_msg:
            return {"success": False, "message": "API Key 无效"}
        if "model_not_found" in error_msg or "No available channel" in error_msg:
            return {"success": False, "message": f"模型 '{config_model}' 不可用"}
        return {"success": False, "message": f"连接失败：{error_msg}"}
