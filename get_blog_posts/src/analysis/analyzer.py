"""博客数据分析器"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

from .models import BlogAnalysisItem


def analyze_by_source(items: List[BlogAnalysisItem]) -> Dict[str, List[BlogAnalysisItem]]:
    """按来源分组"""
    groups: Dict[str, List[BlogAnalysisItem]] = defaultdict(list)
    for item in items:
        groups[item.source].append(item)
    return dict(groups)


def analyze_by_tags(items: List[BlogAnalysisItem]) -> Dict[str, List[BlogAnalysisItem]]:
    """按标签分组"""
    groups: Dict[str, List[BlogAnalysisItem]] = defaultdict(list)
    for item in items:
        for tag in item.tags:
            groups[tag].append(item)
    return dict(groups)


def analyze_by_date(items: List[BlogAnalysisItem]) -> Dict[str, List[BlogAnalysisItem]]:
    """按日期分组（YYYY-MM-DD格式）"""
    groups: Dict[str, List[BlogAnalysisItem]] = defaultdict(list)
    for item in items:
        if item.published_at:
            # 提取日期部分
            date_str = item.published_at[:10] if len(item.published_at) >= 10 else item.published_at
            groups[date_str].append(item)
        elif item.fetched_at:
            date_str = item.fetched_at[:10] if len(item.fetched_at) >= 10 else item.fetched_at
            groups[date_str].append(item)
    return dict(groups)


def extract_keywords(items: List[BlogAnalysisItem], top_n: int = 10) -> List[Tuple[str, int]]:
    """提取关键词（基于标签）"""
    tag_counter = Counter()
    for item in items:
        for tag in item.tags:
            tag_counter[tag] += 1
    return tag_counter.most_common(top_n)


def get_statistics(items: List[BlogAnalysisItem]) -> Dict[str, any]:
    """获取统计信息"""
    stats: Dict[str, any] = {
        "total": len(items),
        "by_source": {},
        "by_date": {},
        "tags_count": 0,
        "with_summary": 0,
        "with_author": 0,
    }
    
    # 按来源统计
    source_groups = analyze_by_source(items)
    stats["by_source"] = {source: len(posts) for source, posts in source_groups.items()}
    
    # 按日期统计
    date_groups = analyze_by_date(items)
    stats["by_date"] = {date: len(posts) for date, posts in sorted(date_groups.items())}
    
    # 标签统计
    all_tags = set()
    for item in items:
        all_tags.update(item.tags)
    stats["tags_count"] = len(all_tags)
    
    # 摘要和作者统计
    for item in items:
        if item.summary:
            stats["with_summary"] += 1
        if item.author:
            stats["with_author"] += 1
    
    return stats


def build_llm_analysis_prompt(items: List[BlogAnalysisItem]) -> str:
    """构建LLM分析提示词"""
    def _clip(txt: str, n: int = 500) -> str:
        if not txt:
            return ""
        return txt[:n] + "..." if len(txt) > n else txt
    
    # 限制数量以避免token过多
    items = items[:100]
    
    # 按来源分组
    source_groups = analyze_by_source(items)
    
    # 构建结构化数据
    lines = [
        "请基于以下博客文章数据生成一份详细的专业中文分析报告，要求：",
        "1) 全中文输出",
        "2) 分层次、结构化分析",
        "3) 提供深入洞察和建议",
        "",
        "分析要求：",
        "- 概览分析：各来源博客的发布情况、主题分布、活跃度",
        "- 主题聚类：识别并分析跨来源的共性主题模式，每个主题提供具体文章支撑",
        "- 趋势洞察：分为短期（最近趋势）、中期（近月模式）、长期（行业方向）",
        "- 内容深度分析：重要文章的亮点、创新点、技术要点",
        "- 行业影响：从技术影响、市场影响、生态影响三个维度分析",
        "- 机会与建议：基于内容分析识别具体的机会点和行动建议",
        "",
        "输出格式：",
        "# 博客内容深度分析报告",
        "",
        "## 一、概览分析",
        "### 1.1 数据概况",
        "...",
        "### 1.2 来源分布",
        "...",
        "### 1.3 主题分布",
        "...",
        "",
        "## 二、主题聚类",
        "### 2.1 主题1：...",
        "...",
        "",
        "## 三、趋势洞察",
        "### 3.1 短期趋势",
        "...",
        "### 3.2 中期趋势",
        "...",
        "### 3.3 长期趋势",
        "...",
        "",
        "## 四、内容深度分析",
        "### 4.1 重要文章亮点",
        "...",
        "### 4.2 技术创新点",
        "...",
        "",
        "## 五、行业影响",
        "### 5.1 技术影响",
        "...",
        "### 5.2 市场影响",
        "...",
        "### 5.3 生态影响",
        "...",
        "",
        "## 六、机会与建议",
        "...",
        "",
        "【博客文章详情】",
        "",
    ]
    
    # 按来源组织数据
    for source, source_items in sorted(source_groups.items()):
        lines.append(f"### 来源: {source} (共 {len(source_items)} 篇)")
        lines.append("")
        
        for i, item in enumerate(source_items[:20], 1):  # 每个来源最多20篇
            info = f"{i}. {_clip(item.title, 150)}"
            
            if item.published_at:
                info += f" | 发布时间: {item.published_at[:10] if len(item.published_at) >= 10 else item.published_at}"
            
            if item.author:
                info += f" | 作者: {_clip(item.author, 50)}"
            
            if item.tags:
                info += f" | 标签: {', '.join(item.tags[:5])}"
            
            if item.summary:
                info += f" | 摘要: {_clip(item.summary, 300)}"
            
            # 添加正文的前500字符
            if item.content:
                content_preview = _clip(item.content.replace("\n", " "), 500)
                info += f" | 内容预览: {content_preview}"
            
            lines.append(info)
        
        lines.append("")
    
    return "\n".join(lines)


def generate_insights_llm(items: List[BlogAnalysisItem], logger: logging.Logger) -> str:
    """使用LLM生成深度洞察"""
    from common.llm import LLMClient
    
    client = LLMClient()
    if not client.api_key:
        logger.warning("未配置 LLM_API_KEY，使用模板化分析")
        return generate_insights_template(items)
    
    try:
        prompt = build_llm_analysis_prompt(items)
        messages = [
            {
                "role": "system",
                "content": "你是资深技术分析员和行业研究员，专注于AI技术领域。请基于提供的博客文章数据，生成深入、全面、有洞察力的分析报告。要求：1) 全中文输出；2) 分层次、结构化分析；3) 提供具体的主题识别、趋势判断、影响评估、机会发现；4) 每个分析点都应有具体文章和数据支撑；5) 洞察应具有前瞻性和可操作性。"
            },
            {"role": "user", "content": prompt},
        ]
        content = client.chat(messages=messages, temperature=0.5)
        if content.strip():
            logger.info("LLM 分析已启用并成功返回")
            return content.strip()
        logger.warning("LLM 返回内容为空，使用模板化分析")
        return generate_insights_template(items)
    except Exception as e:
        logger.exception("LLM 调用失败，使用模板化分析: %s", e)
        return generate_insights_template(items)


def generate_insights_template(items: List[BlogAnalysisItem]) -> str:
    """模板化洞察（当LLM不可用时）"""
    lines: List[str] = []
    
    stats = get_statistics(items)
    
    lines.append("## 一、概览分析")
    lines.append(f"### 1.1 数据概况")
    lines.append(f"- 总文章数: {stats['total']} 篇")
    lines.append(f"- 涉及标签: {stats['tags_count']} 个")
    lines.append(f"- 有摘要: {stats['with_summary']} 篇")
    lines.append(f"- 有作者: {stats['with_author']} 篇")
    lines.append("")
    
    lines.append("### 1.2 来源分布")
    for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {source}: {count} 篇")
    lines.append("")
    
    lines.append("### 1.3 主题分布（标签）")
    keywords = extract_keywords(items, top_n=15)
    for tag, count in keywords:
        lines.append(f"- {tag}: {count} 篇")
    lines.append("")
    
    lines.append("## 二、主题聚类")
    tag_groups = analyze_by_tags(items)
    for tag, tag_items in sorted(tag_groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        lines.append(f"### 2.1 {tag}")
        lines.append(f"共 {len(tag_items)} 篇文章，涉及来源: {', '.join(set(i.source for i in tag_items))}")
        lines.append("重要文章：")
        for item in tag_items[:5]:
            lines.append(f"- {item.title}")
        lines.append("")
    
    lines.append("## 三、建议")
    lines.append("建议启用 LLM 分析功能（配置 LLM_API_KEY）以获得更深入的洞察分析。")
    
    return "\n".join(lines)

