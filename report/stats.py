"""统计和可视化模块"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from .models import NewsAggItem, PaperItem, ReleaseAggItem
from .utils import parse_iso_flexible, sanitize_mermaid_text


def date_range_inclusive(start_dt: datetime, end_dt: datetime) -> List[datetime]:
    """生成包含起止日期的日期列表"""
    days = int((end_dt - start_dt).days)
    return [start_dt + timedelta(days=i) for i in range(days + 1)]


def aggregate_daily_counts(
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
    start_dt: datetime,
    end_dt: datetime,
) -> Dict[str, Dict[str, int]]:
    """聚合每日统计数据"""
    days = date_range_inclusive(start_dt, end_dt)
    fmt = "%Y-%m-%d"
    res: Dict[str, Dict[str, int]] = {
        "papers": {d.strftime(fmt): 0 for d in days},
        "news": {d.strftime(fmt): 0 for d in days},
        "sdk": {d.strftime(fmt): 0 for d in days},
    }
    for p in papers:
        dt = parse_iso_flexible(p.published_at or "")
        if not dt:
            continue
        key = dt.astimezone(timezone.utc).strftime(fmt)
        if key in res["papers"]:
            res["papers"][key] += 1
    for n in news:
        dt = parse_iso_flexible(n.published_at or n.fetched_at or "")
        if not dt:
            continue
        key = dt.astimezone(timezone.utc).strftime(fmt)
        if key in res["news"]:
            res["news"][key] += 1
    for r in releases:
        dt = parse_iso_flexible(r.published_at or "")
        if not dt:
            continue
        key = dt.astimezone(timezone.utc).strftime(fmt)
        if key in res["sdk"]:
            res["sdk"][key] += 1
    return res


def build_mermaid_pie(papers_cnt: int, news_cnt: int, sdk_cnt: int) -> str:
    """构建 Mermaid 饼图"""
    return "\n".join([
        "```mermaid",
        "pie title Source Share",
        f'  "{sanitize_mermaid_text("Papers")}" : {papers_cnt}',
        f'  "{sanitize_mermaid_text("News")}" : {news_cnt}',
        f'  "{sanitize_mermaid_text("SDK Releases")}" : {sdk_cnt}',
        "```",
    ])


def build_mermaid_flow() -> str:
    """构建 Mermaid 流程图"""
    return "\n".join([
        "```mermaid",
        "flowchart LR",
        f'  A[{sanitize_mermaid_text("Read Papers")}] --> B[{sanitize_mermaid_text("Read News")}]',
        f'  B --> C[{sanitize_mermaid_text("Read SDK Releases")}]',
        f'  C --> D[{sanitize_mermaid_text("Aggregate Stats")}]',
        f'  D --> E[{sanitize_mermaid_text("Generate Insights")}]',
        f'  E --> F[{sanitize_mermaid_text("Write Report")}]',
        "```",
    ])

