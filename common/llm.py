from __future__ import annotations

from typing import Dict, List, Optional, Any

from openai import OpenAI

# 使用统一的配置加载器
from common.config_loader import get_env, load_env_config

# 确保加载 .env 文件
load_env_config()


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        # 统一使用 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
        self.api_key = api_key or get_env("LLM_API_KEY")
        self.base_url = base_url or get_env("LLM_BASE_URL", "https://api.deepseek.com")
        self.model = model or get_env("LLM_MODEL", "deepseek-chat")
        self.timeout = timeout or get_env("LLM_TIMEOUT", 60.0, float)
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: Optional[float] = None) -> str:
        """发送聊天消息并返回文本内容"""
        use_model = model or self.model
        kwargs = {
            "model": use_model,
            "messages": messages,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        
        completion = self.client.chat.completions.create(**kwargs)
        return completion.choices[0].message.content or ""

    def chat_json(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> Dict[str, Any]:
        use_model = model or self.model
        completion = self.client.chat.completions.create(
            model=use_model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content or "{}"
        import json

        try:
            return json.loads(content)
        except Exception:
            return {"raw": content}


