"""报告生成器"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .analyzer import (
    analyze_by_date,
    analyze_by_source,
    extract_keywords,
    generate_insights_llm,
    generate_insights_template,
    get_statistics,
)
from .models import BlogAnalysisItem


def write_report(
    path: Path,
    items: List[BlogAnalysisItem],
    start_dt: Optional[datetime],
    end_dt: Optional[datetime],
    use_llm: bool,
    logger: logging.Logger,
) -> None:
    """生成并写入报告"""
    lines: List[str] = []
    
    # 标题
    if start_dt and end_dt:
        date_range = f"{start_dt.strftime('%Y-%m-%d')} 至 {end_dt.strftime('%Y-%m-%d')}"
    else:
        date_range = "全部时间"
    
    lines.append(f"# 博客内容深度分析报告")
    lines.append("")
    lines.append(f"**分析时间范围**: {date_range}")
    lines.append(f"**文章总数**: {len(items)} 篇")
    lines.append("")
    
    # 生成洞察
    if use_llm:
        insights = generate_insights_llm(items, logger)
    else:
        insights = generate_insights_template(items)
    
    # 如果LLM返回的是完整报告，直接使用
    if insights.startswith("# "):
        lines.append(insights)
    else:
        # 否则先添加概览统计，再添加洞察
        stats = get_statistics(items)
        
        lines.append("## 概览统计")
        lines.append("")
        
        # 按来源分组
        source_groups = analyze_by_source(items)
        if source_groups:
            lines.append("### 按来源分布")
            lines.append("")
            for source, source_items in sorted(source_groups.items(), key=lambda x: len(x[1]), reverse=True):
                lines.append(f"- **{source}**: {len(source_items)} 篇")
            lines.append("")
        
        # 按日期分布
        date_groups = analyze_by_date(items)
        if date_groups:
            lines.append("### 按日期分布")
            lines.append("")
            for date_str in sorted(date_groups.keys())[-10:]:  # 最近10天
                count = len(date_groups[date_str])
                lines.append(f"- {date_str}: {count} 篇")
            lines.append("")
        
        # 关键词/标签
        keywords = extract_keywords(items, top_n=15)
        if keywords:
            lines.append("### 热门标签")
            lines.append("")
            for tag, count in keywords:
                lines.append(f"- {tag}: {count} 篇")
            lines.append("")
        
        # 添加深度洞察
        lines.append("## 深度分析")
        lines.append("")
        lines.append(insights)
        lines.append("")
    
    # 详细文章列表
    lines.append("## 文章详情")
    lines.append("")
    
    # 按来源分组展示
    source_groups = analyze_by_source(items)
    for source, source_items in sorted(source_groups.items(), key=lambda x: len(x[1]), reverse=True):
        lines.append(f"### {source} ({len(source_items)} 篇)")
        lines.append("")
        
        # 按日期排序
        source_items_sorted = sorted(
            source_items,
            key=lambda x: (
                x.published_at or x.fetched_at or "",
                x.title
            ),
            reverse=True
        )
        
        for item in source_items_sorted:
            lines.append(f"#### {item.title}")
            lines.append("")
            
            if item.url:
                lines.append(f"- **链接**: {item.url}")
            
            if item.published_at:
                date_str = item.published_at[:10] if len(item.published_at) >= 10 else item.published_at
                lines.append(f"- **发布时间**: {date_str}")
            
            if item.author:
                lines.append(f"- **作者**: {item.author}")
            
            if item.tags:
                lines.append(f"- **标签**: {', '.join(item.tags)}")
            
            if item.summary:
                summary_preview = item.summary[:500] + "..." if len(item.summary) > 500 else item.summary
                lines.append(f"- **摘要**: {summary_preview}")
            
            lines.append("")
    
    # 写入文件
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("报告已生成: %s", str(path))

