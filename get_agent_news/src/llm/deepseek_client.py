from __future__ import annotations

import json
import os
import sys
from typing import Optional, List, Dict, Any
import logging

from src.models import NewsItem


log = logging.getLogger("llm")


def _import_llm_client():
    try:
        from common.llm import LLMClient  # type: ignore
        return LLMClient
    except Exception:
        # 尝试将项目根目录加入 sys.path（.../get_agent_news/src/llm -> 三层上去是项目根）
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
        if root not in sys.path:
            sys.path.append(root)
        from common.llm import LLMClient  # type: ignore
        return LLMClient


LLMClient = _import_llm_client()


class DeepSeekClient:
    def __init__(self) -> None:
        # 使用 common 中统一的环境变量：LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT
        try:
            self.client = LLMClient()
        except Exception as exc:
            log.warning("LLMClient 初始化失败：%s", exc)
            self.client = None

    def available(self) -> bool:
        return bool(getattr(self.client, "api_key", None))

    def score_text(self, title: str, summary: str = "") -> Optional[float]:
        if not self.available():
            return None
        system = {"role": "system", "content": "只输出JSON，不要其他文字"}
        user = {
            "role": "user",
            "content": (
                "你是AI资讯推荐助手，请基于以下标题与摘要，评估其与‘AI Agent/大模型’主题的相关性、时效性与价值度。"
                "输出严格JSON：{\"score\": 0..1}，score越高越值得推荐。\n\n"
                f"标题: {title}\n摘要: {summary or ''}\n"
            ),
        }
        try:
            obj = self.client.chat_json([system, user])  # type: ignore[union-attr]
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
            "请只输出JSON，不要任何解释。\n"
            "允许两种输出格式之一：\n"
            "1) 与输入顺序对应的分数数组，例如: [0.8,0.2,...]\n"
            "2) 带id的对象数组，例如: [{\"id\":0,\"score\":0.8}, ...]\n\n"
            f"输入: {json.dumps(inputs, ensure_ascii=False)}"
        )
        system = {"role": "system", "content": "你是AI资讯推荐助手。严格只输出JSON，不要其他文字。"}
        user = {"role": "user", "content": user_content}
        try:
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)
                req_name = f"llm_request{batch_suffix}.json"
                with open(os.path.join(export_dir, req_name), "w", encoding="utf-8") as f:
                    json.dump({"messages": [system, user]}, f, ensure_ascii=False, indent=2)
            obj = self.client.chat_json([system, user])  # type: ignore[union-attr]
            if export_dir:
                resp_name = f"llm_response{batch_suffix}.json"
                with open(os.path.join(export_dir, resp_name), "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=2)
            parsed = obj
            scores: List[float] = []
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], (int, float)):
                scores = [float(x) for x in parsed]
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                tmp = {int(o.get("id")): float(o.get("score", 0)) for o in parsed if isinstance(o, dict) and "id" in o}
                scores = [tmp.get(i, 0.0) for i in range(len(items))]
            elif isinstance(parsed, dict) and "scores" in parsed:
                arr = parsed.get("scores")
                if isinstance(arr, list):
                    scores = [float(x) for x in arr]
            # 兼容 common.llm 在异常时返回 {"raw": "..."} 的情形
            if not scores and isinstance(parsed, dict) and "raw" in parsed:
                try:
                    raw = parsed.get("raw") or ""
                    arr = json.loads(raw)
                    if isinstance(arr, list) and arr and isinstance(arr[0], (int, float)):
                        scores = [float(x) for x in arr]
                    elif isinstance(arr, list) and arr and isinstance(arr[0], dict):
                        tmp = {int(o.get("id")): float(o.get("score", 0)) for o in arr if isinstance(o, dict) and "id" in o}
                        scores = [tmp.get(i, 0.0) for i in range(len(items))]
                    elif isinstance(arr, dict) and "scores" in arr and isinstance(arr["scores"], list):
                        scores = [float(x) for x in arr["scores"]]
                except Exception:
                    scores = []
            if len(scores) != len(items):
                log.warning("LLM 返回分数数量不匹配: expected=%s got=%s", len(items), len(scores))
                return None
            scores = [0.0 if s < 0 else 1.0 if s > 1 else s for s in scores]
            return scores
        except Exception as exc:
            log.exception("LLM 打分解析失败: %s", exc)
            return None
