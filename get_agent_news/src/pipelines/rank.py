from __future__ import annotations

import logging
from typing import List, Optional
from datetime import datetime, timezone

from src.models import NewsItem
from src.llm.deepseek_client import DeepSeekClient

log = logging.getLogger("rank")


def _heuristic_score(item: NewsItem) -> float:
    title = (item.title or "").lower()
    score = 0.0
    keywords = [
        ("agent", 0.25),
        ("大模型", 0.25),
        ("llm", 0.2),
        ("生成式", 0.1),
        ("ai", 0.05),
    ]
    for k, w in keywords:
        if k in title:
            score += w
    ts = item.published_at or item.fetched_at
    age_days = (datetime.now(timezone.utc) - ts).days
    if age_days <= 1:
        score += 0.2
    elif age_days <= 3:
        score += 0.1
    priors = {
        "机器之心": 0.1,
        "雷峰网": 0.1,
        "InfoQ 中文站": 0.1,
        "阿里云开发者社区（AI）": 0.1,
        "腾讯云开发者（AI）": 0.1,
        "36氪（AI）": 0.1,
        "AIbase 资讯": 0.1,
    }
    score += priors.get(item.source, 0.0)
    return max(0.0, min(1.0, score))


def rank_items(items: List[NewsItem], export_dir: Optional[str] = None, batch_size: int = 30) -> List[NewsItem]:
    client = DeepSeekClient()
    use_llm = client.available()

    if use_llm:
        log.info("使用 DeepSeek 批量打分（每批 %s 条）", batch_size)
        for start in range(0, len(items), batch_size):
            end = min(start + batch_size, len(items))
            batch = items[start:end]
            suffix = f"_{start // batch_size + 1}"
            scores = client.score_batch(batch, export_dir=export_dir, batch_suffix=suffix)
            if scores is None:
                log.warning("批 %s 打分失败，使用启发式回退", suffix)
                for it in batch:
                    it.score = _heuristic_score(it)
            else:
                for it, sc in zip(batch, scores):
                    it.score = sc
    else:
        log.info("未配置 DEEPSEEK_API_KEY，使用启发式打分")
        for it in items:
            it.score = _heuristic_score(it)

    items.sort(key=lambda x: (x.score or 0.0), reverse=True)
    return items
