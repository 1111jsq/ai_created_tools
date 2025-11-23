"""洞察生成模块"""

from __future__ import annotations

import logging
from typing import List

from .models import NewsAggItem, PaperItem, ReleaseAggItem


def generate_insights(
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
) -> str:
    """模板化洞察（当LLM不可用时）"""
    lines: List[str] = []
    lines.append("- 本期论文、资讯与 SDK 更新数量已在概览展示。")
    if papers:
        lines.append(f"- 论文样本数 {len(papers)}，建议关注排名靠前与机构背景的论文。")
    else:
        lines.append("- 论文数据缺失，综合判断可能受抓取/时间窗口影响。")
    if news:
        lines.append(f"- 资讯样本数 {len(news)}，建议筛选来源可靠、标签匹配度高的条目。")
    else:
        lines.append("- 资讯数据缺失，建议检查来源配置或抓取窗口。")
    if releases:
        repos = {}
        for r in releases:
            repos[r.repo] = repos.get(r.repo, 0) + 1
        top_repos = sorted(repos.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_repos:
            lines.append("- SDK 活跃仓库 Top: " + ", ".join([f"{k}:{v}" for k, v in top_repos]))
    else:
        lines.append("- SDK 更新数据缺失，可能是时间窗口或限额导致。")
    lines.append("- 若启用 LLM，可生成更深入的趋势洞察与建议。")
    return "\n".join(lines)


def build_llm_prompt(
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
) -> str:
    """构建LLM提示词"""
    def _clip(txt: str, n: int = 200) -> str:
        return (txt or "")[:n]
    # Limit items to keep prompt small
    p_lines = [f"- { _clip(p.title) }" for p in papers[:50]]
    n_lines = [f"- { _clip(n.title) } ({_clip(n.source)} {_clip(','.join(n.tags or []))})" for n in news[:50]]
    r_lines = [f"- { _clip(r.repo) } { _clip(r.tag) } { _clip(r.name) }" for r in releases[:50]]
    parts = [
        "请基于以下样本生成本期的趋势洞察、主题聚类、重要变更影响与对团队的建议，要求：",
        "1) 全中文；2) 分点列出；3) 不输出任何 Mermaid 文本；4) 若数据源缺失需声明局限。",
        "",
        "【论文样本】",
        *p_lines,
        "",
        "【资讯样本】",
        *n_lines,
        "",
        "【SDK Releases 样本】",
        *r_lines,
    ]
    return "\n".join(parts)


def generate_insights_llm(
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
    logger: logging.Logger,
) -> str:
    """使用LLM生成洞察"""
    from common.llm import LLMClient
    
    client = LLMClient()
    if not client.api_key:
        return generate_insights(papers, news, releases)
    
    try:
        prompt = build_llm_prompt(papers, news, releases)
        messages = [
            {"role": "system", "content": "你是资深技术分析员，请用中文输出深度洞察。"},
            {"role": "user", "content": prompt},
        ]
        content = client.chat(messages=messages, temperature=0.4)
        if content.strip():
            logger.info("LLM 分析已启用并成功返回。")
            return content.strip()
        logger.warning("LLM 返回内容为空，使用模板化洞察。")
        return generate_insights(papers, news, releases)
    except Exception as e:
        logger.exception("LLM 调用失败，使用模板化洞察: %s", e)
        return generate_insights(papers, news, releases)

