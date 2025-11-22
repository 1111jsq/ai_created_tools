from __future__ import annotations

import json
import logging
from typing import Dict, List

from agents_papers.models.paper import Paper
from common.llm import LLMClient

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "你是一位学术研究助理。请阅读论文题目与摘要，给出结构化要点："
    "1. 研究问题 2. 方法 3. 实验设置 4. 结果与贡献 5. 局限与未来工作。"
    "输出为JSON，字段: problem, method, experiments, results, limitations, novelty_score(0-5)，内容要求以中文输出。"
)


def analyze_with_llm(papers: List[Paper], budget: int = 20) -> List[Dict[str, object]]:
    client = LLMClient()
    if not client.api_key:
        logger.warning("LLM_API_KEY 未设置，跳过大模型分析")
        return []

    results: List[Dict[str, object]] = []
    limited = papers[:budget]
    # 构造批量输入
    items = []
    for p in limited:
        items.append({
            "paperId": p.paperId,
            "title": p.title,
            "authors": p.authors,
            "venue": p.venue or "",
            "year": p.year or 0,
            "month": p.month or 0,
            "abstract": p.abstract,
        })

    user_content = (
        "你将收到一个论文条目列表 items。请逐条分析，每条输出一个对象，"
        "包含 paperId 与 analysis。analysis 的字段为: problem, method, experiments, results, limitations, novelty_score(0-5)。"
        "所有文本字段使用中文，novelty_score 为数字。最终返回 JSON 对象 {\"analyses\": [...]}，"
        "其中 analyses 是与输入顺序一致的数组。\n\n"
        f"items: {json.dumps(items, ensure_ascii=False)}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    parsed = client.chat_json(messages)

    analyses = parsed.get("analyses")
    if isinstance(analyses, list):
        mapping: Dict[str, object] = {}
        for item in analyses:
            pid = item.get("paperId") if isinstance(item, dict) else None
            if pid:
                mapping[pid] = item.get("analysis", {})
        for p in limited:
            results.append({
                "paperId": p.paperId,
                "analysis": mapping.get(p.paperId, {}),
            })
        return results

    if isinstance(parsed, dict):
        for p in limited:
            results.append({
                "paperId": p.paperId,
                "analysis": parsed.get(p.paperId, {}),
            })
        return results

    # 最差情况
    content = parsed if isinstance(parsed, str) else json.dumps(parsed, ensure_ascii=False)
    for p in limited:
        results.append({
            "paperId": p.paperId,
            "analysis": {"raw": content},
        })
    return results


