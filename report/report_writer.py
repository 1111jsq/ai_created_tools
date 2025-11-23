"""报告写入模块"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .insights import generate_insights, generate_insights_llm
from .models import NewsAggItem, PaperItem, ReleaseAggItem
from .processors import count_products_in_news, extract_paper_details, identify_important_news


def write_report(
    path: Path,
    label: str,
    start_dt: datetime,
    end_dt: datetime,
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
    daily_counts: Dict[str, Dict[str, int]],
    use_llm: bool,
    logger: logging.Logger,
    execution_timeline: Optional[List[Tuple[str, datetime]]] = None,
    enable_image_generation: bool = True,
    position_to_image: Optional[Dict[str, str]] = None,
) -> None:
    """写入报告到文件"""
    total_papers = len(papers)
    total_news = len(news)
    total_sdk = len(releases)
    if use_llm:
        insights = generate_insights_llm(papers, news, releases, logger)
    else:
        insights = generate_insights(papers, news, releases)
    
    lines: List[str] = []
    lines.append(f"# 智能体每周/区间报告（{label}）")
    lines.append("")
    lines.append("## 概览")
    lines.append(f"- 时间范围: {start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}")
    lines.append(f"- 论文: {total_papers}  条")
    lines.append(f"- 资讯: {total_news}  条")
    lines.append(f"- SDK 更新: {total_sdk}  条")
    lines.append("")
    
    # 插入图片（在概览后）
    if position_to_image and "after_overview" in position_to_image:
        lines.append(f"![概览图表]({position_to_image['after_overview']})")
        lines.append("")

    # Papers
    lines.append("## 论文")
    if papers:
        # 使用LLM提取论文功能和核心内容
        papers_with_details = extract_paper_details(papers[:20], logger, use_llm)
        
        # 按功能分组
        feature_groups: Dict[str, List[Dict[str, Any]]] = {}
        for paper_detail in papers_with_details:
            feature = paper_detail.get("feature", "其他")
            if feature not in feature_groups:
                feature_groups[feature] = []
            feature_groups[feature].append(paper_detail)
        
        # 插入图片（在论文前）
        if position_to_image and "after_papers" in position_to_image:
            lines.append(f"![论文功能分布图表]({position_to_image['after_papers']})")
            lines.append("")
        
        # 合并所有论文到一个表格（按功能排序，相同功能的论文在一起）
        lines.append("| 功能 | 论文标题 | 核心内容 |")
        lines.append("|------|---------|---------|")
        # 先按功能分组排序，再按论文排序
        sorted_features = sorted(feature_groups.items(), key=lambda x: (len(x[1]), x[0]), reverse=True)
        for feature, paper_list in sorted_features:
            for paper_detail in paper_list:
                title = paper_detail.get("title", "")
                core_content = paper_detail.get("core_content", "")
                # 限制长度以便表格显示
                title_short = title[:65] + "..." if len(title) > 65 else title
                core_short = core_content[:130] + "..." if len(core_content) > 130 else core_content
                lines.append(f"| {feature} | {title_short} | {core_short} |")
        lines.append("")
    else:
        lines.append("- 数据缺失或不在时间范围内。")
    lines.append("")

    # News
    lines.append("## 资讯")
    if news:
        # 统计产品数量
        product_count = count_products_in_news(news)
        lines.append(f"**涉及产品数量**: {product_count} 个")
        lines.append("")
        
        # 识别重要资讯（使用LLM或基于关键词）
        important_news = identify_important_news(news[:30], logger, use_llm)
        important_titles = {n.title for n in important_news}
        
        # 插入图片（在资讯前）
        if position_to_image and "after_news" in position_to_image:
            lines.append(f"![资讯产品分布图表]({position_to_image['after_news']})")
            lines.append("")
        
        # 使用表格展示资讯（去除来源和标签列，添加摘要）
        lines.append("| 资讯标题 | 摘要/核心内容 |")
        lines.append("|---------|-------------|")
        for n in news[:30]:
            title = n.title
            # 重要资讯标粗
            if n.title in important_titles:
                title = f"**{title}**"
            
            # 提取摘要（从tags中提取，格式为"摘要: xxx"）
            summary = ""
            if n.tags:
                for tag in n.tags:
                    if tag.startswith("摘要: "):
                        summary = tag.replace("摘要: ", "").strip()
                        break
            
            # 如果没有摘要，尝试从标题生成简短描述
            if not summary:
                # 简单提取：如果标题包含"发布"、"开源"等关键词，生成简短描述
                if "发布" in title or "开源" in title:
                    summary = "产品发布或开源相关资讯"
                elif "AI" in title or "智能" in title:
                    summary = "AI技术相关资讯"
                else:
                    summary = "（暂无摘要）"
            
            # 限制长度
            title_short = title[:70] + "..." if len(title) > 70 else title
            summary_short = summary[:180] + "..." if len(summary) > 180 else summary
            lines.append(f"| {title_short} | {summary_short} |")
        lines.append("")
    else:
        lines.append("- 数据缺失或不在时间范围内。")
    lines.append("")

    # SDK
    lines.append("## SDK 更新")
    if releases:
        # 按仓库分组
        repo_groups: Dict[str, List[ReleaseAggItem]] = {}
        for r in releases:
            if r.repo not in repo_groups:
                repo_groups[r.repo] = []
            repo_groups[r.repo].append(r)
        
        # 按仓库展示，每个仓库展示其更新
        for repo, repo_releases in sorted(repo_groups.items()):
            lines.append(f"### {repo}")
            for r in repo_releases[:10]:  # 每个仓库最多显示10个版本
                lines.append(f"#### {r.tag} - {r.name}")
                lines.append(f"- **发布时间**: {r.published_at[:10] if len(r.published_at) >= 10 else r.published_at}")
                if r.highlights:
                    lines.append("- **主要变更**:")
                    for highlight in r.highlights[:5]:  # 最多显示5条变更
                        lines.append(f"  - {highlight}")
                else:
                    lines.append("- **主要变更**: 无详细信息")
                lines.append("")
    else:
        lines.append("- 数据缺失或不在时间范围内。")
    lines.append("")
    
    # 插入图片（在 SDK 后）
    if position_to_image and "after_sdk" in position_to_image:
        lines.append(f"![SDK 相关图表]({position_to_image['after_sdk']})")
        lines.append("")

    # Insights
    lines.append("## 综合洞察")
    
    # 插入图片（在洞察内容前，但确保图片路径正确）
    if position_to_image and "in_insights" in position_to_image:
        img_path = position_to_image['in_insights']
        # 确保图片路径存在
        img_full_path = path.parent / img_path
        if img_full_path.exists() and img_full_path.stat().st_size > 0:
            lines.append(f"![洞察图表]({img_path})")
            lines.append("")
        else:
            logger.warning("洞察图表文件不存在或为空: %s", img_full_path)
    
    lines.append(insights)

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("报告已生成: %s", str(path))

