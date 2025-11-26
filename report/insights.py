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
    """构建LLM提示词，提供丰富的上下文信息"""
    def _clip(txt: str, n: int = 300) -> str:
        return (txt or "")[:n]
    
    def _format_authors(authors) -> str:
        """格式化作者信息"""
        if not authors:
            return "未知"
        if isinstance(authors, list):
            return ", ".join(authors[:3])
        return str(authors)
    
    def _format_tags(tags) -> str:
        """格式化标签信息"""
        if not tags:
            return ""
        if isinstance(tags, list):
            return ", ".join(tags[:5])
        return str(tags)
    
    # 限制数量以避免token过多
    papers = papers[:50]
    news = news[:50]
    releases = releases[:30]
    
    # 构建论文结构化数据
    p_lines = []
    for i, p in enumerate(papers, 1):
        authors_str = _format_authors(p.authors)
        tags_str = _format_tags(p.tags)
        published_str = p.published_at[:10] if p.published_at and len(p.published_at) >= 10 else "未知"
        rank_str = f", 排名: {p.rank}" if p.rank else ""
        score_str = f", 评分: {p.score:.2f}" if p.score else ""
        
        paper_info = f"{i}. {_clip(p.title)}"
        paper_info += f" | 作者: {_clip(authors_str, 100)}"
        paper_info += f" | 发布时间: {published_str}"
        if tags_str:
            paper_info += f" | 标签: {_clip(tags_str, 100)}"
        if rank_str:
            paper_info += rank_str
        if score_str:
            paper_info += score_str
        p_lines.append(paper_info)
    
    # 构建资讯结构化数据（提取摘要和产品）
    n_lines = []
    for i, n in enumerate(news, 1):
        # 提取摘要
        summary = ""
        if n.tags:
            for tag in n.tags:
                if tag.startswith("摘要: "):
                    summary = tag.replace("摘要: ", "").strip()
                    break
        
        # 提取产品
        products = []
        title_lower = n.title.lower()
        product_keywords_map = {
            "OpenAI": ["openai", "gpt", "chatgpt", "sora"],
            "Anthropic": ["anthropic", "claude"],
            "Google": ["google", "gemini", "notebooklm"],
            "Meta": ["meta", "dreamgym"],
            "Microsoft": ["microsoft", "copilot"],
            "小米": ["小米", "mimo"],
            "蚂蚁": ["蚂蚁", "灵光"],
        }
        for product, keywords in product_keywords_map.items():
            if any(kw in title_lower for kw in keywords):
                products.append(product)
                if len(products) >= 2:
                    break
        
        products_str = ", ".join(products) if products else "未知"
        published_str = n.published_at[:10] if n.published_at and len(n.published_at) >= 10 else "未知"
        source_str = _clip(n.source, 50)
        tags_str = _format_tags([t for t in (n.tags or []) if not t.startswith("摘要: ")])
        
        news_info = f"{i}. {_clip(n.title, 150)}"
        news_info += f" | 发布时间: {published_str}"
        news_info += f" | 来源: {source_str}"
        news_info += f" | 产品: {products_str}"
        if summary:
            news_info += f" | 摘要: {_clip(summary, 200)}"
        if tags_str:
            news_info += f" | 标签: {_clip(tags_str, 100)}"
        n_lines.append(news_info)
    
    # 构建SDK结构化数据
    r_lines = []
    for i, r in enumerate(releases, 1):
        published_str = r.published_at[:10] if r.published_at and len(r.published_at) >= 10 else "未知"
        highlights_str = ""
        if r.highlights:
            highlights_str = "; ".join(r.highlights[:3])
        
        release_info = f"{i}. {_clip(r.repo, 80)}"
        release_info += f" | 版本: {_clip(r.tag, 30)}"
        release_info += f" | 名称: {_clip(r.name, 100)}"
        release_info += f" | 发布时间: {published_str}"
        if highlights_str:
            release_info += f" | 主要变更: {_clip(highlights_str, 200)}"
        r_lines.append(release_info)
    
    # 构建完整的提示词
    parts = [
        "请基于以下结构化数据生成本期的深度洞察分析，要求：",
        "1) 全中文输出",
        "2) 分层次、结构化分析",
        "3) 不输出任何 Mermaid 代码块",
        "4) 若数据源缺失需声明局限",
        "",
        "分析要求：",
        "- 趋势洞察：分为短期（本周趋势）、中期（近月模式）、长期（行业方向）三个层次",
        "- 主题聚类：识别并分析跨论文、资讯、SDK的共性主题模式，每个主题提供数据支撑",
        "- 影响分析：从技术影响、市场影响、产业影响三个维度分析",
        "- 机会识别：基于数据和趋势识别具体的机会点",
        "- 风险评估：识别潜在的技术风险、市场风险、合规风险等",
        "",
        "输出格式：",
        "### 趋势洞察",
        "#### 短期趋势（本周）",
        "...",
        "#### 中期趋势（近月）",
        "...",
        "#### 长期趋势（行业方向）",
        "...",
        "",
        "### 主题聚类",
        "1. 主题1：...",
        "",
        "### 影响分析",
        "#### 技术影响",
        "...",
        "#### 市场影响",
        "...",
        "#### 产业影响",
        "...",
        "",
        "### 机会识别",
        "...",
        "",
        "### 风险评估",
        "...",
        "",
        "【论文详情（标题、作者、机构、标签、发布时间、排名、评分）】",
        *p_lines,
        "",
        "【资讯详情（标题、发布时间、来源、产品、完整摘要、标签）】",
        *n_lines,
        "",
        "【SDK Releases详情（仓库、版本、发布时间、主要变更）】",
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
            {
                "role": "system",
                "content": "你是资深技术分析员和行业研究员，专注于AI智能体和大模型领域。请基于提供的结构化数据，生成深入、全面、有洞察力的分析报告。要求：1) 全中文输出；2) 分层次、结构化分析；3) 提供具体的趋势判断、主题识别、影响评估、机会发现和风险评估；4) 每个分析点都应有数据支撑；5) 洞察应具有前瞻性和可操作性。"
            },
            {"role": "user", "content": prompt},
        ]
        content = client.chat(messages=messages, temperature=0.5)
        if content.strip():
            logger.info("LLM 分析已启用并成功返回。")
            return content.strip()
        logger.warning("LLM 返回内容为空，使用模板化洞察。")
        return generate_insights(papers, news, releases)
    except Exception as e:
        logger.exception("LLM 调用失败，使用模板化洞察: %s", e)
        return generate_insights(papers, news, releases)

