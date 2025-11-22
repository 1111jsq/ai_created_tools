from __future__ import annotations

import json
import os
from typing import Optional, List, Dict, Any
import logging

import requests

from src.config import get_deepseek_config
from src.models import NewsItem


log = logging.getLogger("llm")


class DeepSeekClient:
    def __init__(self) -> None:
        cfg = get_deepseek_config()
        self.api_key = cfg.get("api_key", "")
        self.base_url = cfg.get("base_url", "https://api.deepseek.com").rstrip("/")
        self.model = cfg.get("default_model", "deepseek-chat")
        self.timeout = int(cfg.get("timeout", 60))

    def available(self) -> bool:
        return bool(self.api_key)

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def score_text(self, title: str, summary: str = "") -> Optional[float]:
        if not self.available():
            return None
        prompt = (
            "你是AI资讯推荐助手，请基于以下标题与摘要，评估其与‘AI Agent/大模型’主题的相关性、时效性与价值度。"
            "输出严格JSON：{\\'score\\'': 0..1}，score越高越值得推荐。\\n\\n"
            f"标题: {title}\\n摘要: {summary or ''}\\n"
        )
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "只输出JSON，不要其他文字"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 200,
            }
            data = self._post(payload)
            content = data["choices"][0]["message"]["content"].strip()
            obj = json.loads(content)
            score = float(obj.get("score", 0))
            if score < 0:
                score = 0.0
            if score > 1:
                score = 1.0
            return score
        except Exception:
            return None

    def score_batch(self, items: List[NewsItem], export_dir: Optional[str] = None, batch_suffix: str = "") -> Optional[List[float]]:
        if not self.available():
            return None
        inputs = []
        for idx, it in enumerate(items):
            summary = (it.summary or "")
            if len(summary) > 200:
                summary = summary[:200]
            inputs.append({
                "id": idx,
                "source": it.source,
                "title": it.title,
                "summary": summary,
            })
        user_content = (
            "对以下新闻项进行打分，每项输出0到1之间的小数，越高越值得推荐。"
            "请只输出JSON，不要任何解释。\\n"
            "允许两种输出格式之一：\\n"
            "1) 与输入顺序对应的分数数组，例如: [0.8,0.2,...] \\n"
            "2) 带id的对象数组，例如: [{\\\'id\\\':0,\\'score\\':0.8}, ...] \\n\\n"
            f"输入: {json.dumps(inputs, ensure_ascii=False)}"
        )
        log.debug("LLM 请求构造完成: items=%s chars=%s", len(items), len(user_content))
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是AI资讯推荐助手。严格只输出JSON，不要其他文字。"},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }
        try:
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)
                req_name = f"llm_request{batch_suffix}.json"
                with open(os.path.join(export_dir, req_name), "w", encoding="utf-8") as f:
                    json.dump({"model": self.model, "messages": payload["messages"]}, f, ensure_ascii=False, indent=2)
            data = self._post(payload)
            content = data["choices"][0]["message"]["content"].strip()
            log.debug("LLM 响应长度: %s 字符", len(content))
            if export_dir:
                resp_name = f"llm_response{batch_suffix}.json"
                with open(os.path.join(export_dir, resp_name), "w", encoding="utf-8") as f:
                    f.write(content)
            parsed = json.loads(content)
            scores: List[float] = []
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], (int, float)):
                scores = [float(x) for x in parsed]
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                tmp = {int(obj.get("id")): float(obj.get("score", 0)) for obj in parsed if "id" in obj}
                scores = [tmp.get(i, 0.0) for i in range(len(items))]
            elif isinstance(parsed, dict) and "scores" in parsed:
                arr = parsed.get("scores")
                if isinstance(arr, list):
                    scores = [float(x) for x in arr]
            if len(scores) != len(items):
                log.warning("LLM 返回分数数量不匹配: expected=%s got=%s", len(items), len(scores))
                return None
            scores = [0.0 if s < 0 else 1.0 if s > 1 else s for s in scores]
            return scores
        except Exception as exc:
            log.exception("LLM 打分解析失败: %s", exc)
            return None
