from __future__ import annotations

import os
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from openai import OpenAI

# 统一环境变量：LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT
load_dotenv()


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.model = model or os.getenv("LLM_MODEL", "deepseek-chat")
        self.timeout = timeout or float(os.getenv("LLM_TIMEOUT", "60"))
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

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


