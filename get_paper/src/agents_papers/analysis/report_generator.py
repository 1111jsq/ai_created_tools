from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from agents_papers.analysis.statistics import AdvancedStatsReport, StatsReport
from agents_papers.models.paper import Paper


def generate_comprehensive_report(
    papers: List[Paper],
    stats: StatsReport,
    advanced_stats: AdvancedStatsReport,
    analyses: List[Dict[str, object]],
    ranked_papers: List[Tuple[Paper, Dict[str, object] | None, float]],
    top_papers: List[Tuple[Paper, Dict[str, object] | None]],
    label: str,
) -> str:
    """生成全面的智能体分析报告"""
    lines: List[str] = []

    # 标题
    lines.append(f"# AI智能体研究分析报告 - {label}")
    lines.append("")

    # 执行摘要
    lines.extend(_generate_executive_summary(papers, stats, top_papers))
    lines.append("")

    # 基础统计
    lines.extend(_generate_statistics_section(stats))
    lines.append("")

    # 技术分类分析
    lines.extend(_generate_technical_classification(papers, advanced_stats))
    lines.append("")

    # 研究趋势
    lines.extend(_generate_research_trends(papers, advanced_stats))
    lines.append("")

    # 热点话题
    lines.extend(_generate_hot_topics(papers, advanced_stats))
    lines.append("")

    # 方法学分析
    lines.extend(_generate_methodology_analysis(analyses))
    lines.append("")

    # 应用场景
    lines.extend(_generate_application_scenarios(papers))
    lines.append("")

    # Top论文推荐
    lines.extend(_generate_top_papers_section(top_papers))
    lines.append("")

    # 研究问题聚类
    lines.extend(_generate_research_problems(analyses))
    lines.append("")

    # 局限性与未来方向
    lines.extend(_generate_limitations_future(analyses))
    lines.append("")

    # 作者与机构
    lines.extend(_generate_author_analysis(papers, stats))
    lines.append("")

    # 数据源分析
    lines.extend(_generate_source_analysis(papers, advanced_stats))
    lines.append("")

    return "\n".join(lines)


def _generate_executive_summary(
    papers: List[Paper],
    stats: StatsReport,
    top_papers: List[Tuple[Paper, Dict[str, object] | None]],
) -> List[str]:
    """生成执行摘要"""
    lines: List[str] = []
    lines.append("## 执行摘要")
    lines.append("")

    # 总体概况
    lines.append(f"本报告分析了 **{stats.total}** 篇AI智能体相关论文，涵盖多个研究方向和主题。")
    lines.append("")

    # 关键发现
    lines.append("### 关键发现")
    lines.append("")

    # Top标签
    if stats.top_tags:
        top_tag = stats.top_tags[0]
        lines.append(f"- **最热门研究方向**: {top_tag[0]} ({top_tag[1]}篇论文)")
    
    # Top主题
    if stats.topics_distribution:
        top_topic = stats.topics_distribution[0]
        lines.append(f"- **主要研究领域**: {top_topic[0]} ({top_topic[1]}篇论文)")

    # 高评分论文数量（从 analysis 中获取 novelty_score）
    high_score_count = 0
    for paper, analysis in top_papers:
        if analysis and isinstance(analysis, dict):
            novelty_score = analysis.get("novelty_score")
            if isinstance(novelty_score, (int, float)) and novelty_score >= 3.0:
                high_score_count += 1
    if high_score_count > 0:
        lines.append(f"- **高质量论文**: {high_score_count}篇论文获得较高评分（≥3.0）")

    lines.append("")

    return lines


def _generate_statistics_section(stats: StatsReport) -> List[str]:
    """生成基础统计部分"""
    lines: List[str] = []
    lines.append("## 基础统计")
    lines.append("")

    lines.append(f"### 论文总数")
    lines.append(f"- **总计**: {stats.total} 篇")
    lines.append("")

    # 作者统计
    lines.append("### 作者统计")
    if stats.top_authors:
        lines.append("| 排名 | 作者 | 论文数 |")
        lines.append("|------|------|--------|")
        for idx, (author, count) in enumerate(stats.top_authors[:10], 1):
            lines.append(f"| {idx} | {author} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    # 标签统计
    lines.append("### 标签统计")
    if stats.top_tags:
        lines.append("| 排名 | 标签 | 论文数 |")
        lines.append("|------|------|--------|")
        for idx, (tag, count) in enumerate(stats.top_tags[:10], 1):
            lines.append(f"| {idx} | {tag} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    # 主题分布
    lines.append("### 主题分布")
    if stats.topics_distribution:
        lines.append("| 主题 | 论文数 |")
        lines.append("|------|--------|")
        for topic, count in stats.topics_distribution:
            lines.append(f"| {topic} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    return lines


def _generate_technical_classification(
    papers: List[Paper],
    advanced_stats: AdvancedStatsReport,
) -> List[str]:
    """生成技术分类分析"""
    lines: List[str] = []
    lines.append("## 技术分类分析")
    lines.append("")

    # 标签共现分析
    lines.append("### 标签共现分析")
    if advanced_stats.tag_cooccurrence:
        lines.append("以下标签经常同时出现在同一篇论文中：")
        lines.append("")
        lines.append("| 标签对 | 共现次数 |")
        lines.append("|--------|----------|")
        for (tag1, tag2), count in advanced_stats.tag_cooccurrence[:10]:
            lines.append(f"| {tag1} + {tag2} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    # 主题-标签关联
    lines.append("### 主题-标签关联")
    if advanced_stats.topic_tag_association:
        for topic, tag_list in advanced_stats.topic_tag_association.items():
            lines.append(f"#### {topic}")
            if tag_list:
                lines.append("| 标签 | 论文数 |")
                lines.append("|------|--------|")
                for tag, count in tag_list[:5]:
                    lines.append(f"| {tag} | {count} |")
            lines.append("")
    else:
        lines.append("暂无数据")
    lines.append("")

    return lines


def _generate_research_trends(
    papers: List[Paper],
    advanced_stats: AdvancedStatsReport,
) -> List[str]:
    """生成研究趋势分析"""
    lines: List[str] = []
    lines.append("## 研究趋势")
    lines.append("")

    # 时间分布
    lines.append("### 时间分布")
    if advanced_stats.time_distribution:
        sorted_times = sorted(advanced_stats.time_distribution.items())
        lines.append("| 时间 | 论文数 |")
        lines.append("|------|--------|")
        for time_key, count in sorted_times:
            lines.append(f"| {time_key} | {count} |")
    else:
        lines.append("暂无时间数据")
    lines.append("")

    # 标签趋势（按时间）
    lines.append("### 标签趋势分析")
    tag_time_counter: Dict[str, Counter[str]] = defaultdict(Counter)
    for p in papers:
        if p.year and p.month:
            time_key = f"{p.year}-{p.month:02d}"
            for tag in p.tags:
                tag_time_counter[tag][time_key] += 1

    if tag_time_counter:
        for tag, time_counter in list(tag_time_counter.items())[:5]:
            lines.append(f"#### {tag}")
            sorted_times = sorted(time_counter.items())
            lines.append("| 时间 | 论文数 |")
            lines.append("|------|--------|")
            for time_key, count in sorted_times:
                lines.append(f"| {time_key} | {count} |")
            lines.append("")
    else:
        lines.append("暂无数据")
    lines.append("")

    return lines


def _generate_hot_topics(
    papers: List[Paper],
    advanced_stats: AdvancedStatsReport,
) -> List[str]:
    """生成热点话题识别"""
    lines: List[str] = []
    lines.append("## 热点话题")
    lines.append("")

    # 高频关键词（从标题和摘要提取）
    keyword_counter: Counter[str] = Counter()
    keywords = [
        "agent", "multi-agent", "llm", "reasoning", "planning", "tool", "autonomous",
        "benchmark", "evaluation", "memory", "retrieval", "reflection", "workflow",
        "reinforcement", "learning", "transformer", "gpt", "claude", "gemini"
    ]

    for p in papers:
        text = f"{p.title} {p.abstract}".lower()
        for kw in keywords:
            if kw in text:
                keyword_counter[kw] += 1

    if keyword_counter:
        lines.append("### 高频关键词")
        lines.append("| 关键词 | 出现次数 |")
        lines.append("|--------|----------|")
        for kw, count in keyword_counter.most_common(15):
            lines.append(f"| {kw} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    # 新兴标签（出现频率较低但值得关注）
    tag_counter = Counter()
    for p in papers:
        tag_counter.update(p.tags)

    emerging_tags = [(tag, count) for tag, count in tag_counter.items() if 1 <= count <= 3]
    if emerging_tags:
        lines.append("### 新兴研究方向")
        lines.append("以下标签出现频率较低，可能是新兴研究方向：")
        lines.append("")
        for tag, count in sorted(emerging_tags, key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"- **{tag}**: {count}篇")
    lines.append("")

    return lines


def _generate_methodology_analysis(analyses: List[Dict[str, object]]) -> List[str]:
    """生成方法学分析"""
    lines: List[str] = []
    lines.append("## 方法学分析")
    lines.append("")

    methods: List[str] = []
    for analysis_item in analyses:
        analysis = analysis_item.get("analysis", {})
        if isinstance(analysis, dict):
            method = analysis.get("method", "")
            if method and isinstance(method, str):
                methods.append(method)

    if methods:
        lines.append("基于LLM分析，主要研究方法包括：")
        lines.append("")
        # 提取关键词
        method_keywords: Counter[str] = Counter()
        keywords = [
            "强化学习", "监督学习", "无监督学习", "迁移学习", "元学习",
            "神经网络", "transformer", "注意力机制", "微调", "预训练",
            "多模态", "视觉", "语言", "推理", "规划", "搜索"
        ]

        for method_text in methods:
            method_lower = method_text.lower()
            for kw in keywords:
                if kw in method_lower:
                    method_keywords[kw] += 1

        if method_keywords:
            lines.append("### 研究方法关键词统计")
            lines.append("| 关键词 | 出现次数 |")
            lines.append("|--------|----------|")
            for kw, count in method_keywords.most_common(10):
                lines.append(f"| {kw} | {count} |")
        else:
            lines.append("暂无方法学关键词数据")
    else:
        lines.append("暂无LLM分析方法学数据")
    lines.append("")

    return lines


def _generate_application_scenarios(papers: List[Paper]) -> List[str]:
    """生成应用场景分析"""
    lines: List[str] = []
    lines.append("## 应用场景分析")
    lines.append("")

    # 从标题和摘要中提取应用场景关键词
    scenario_keywords = [
        "code", "programming", "software", "math", "mathematics", "reasoning",
        "web", "browser", "search", "qa", "question answering", "chat",
        "robot", "robotics", "control", "game", "gaming", "simulation",
        "medical", "healthcare", "education", "finance", "business"
    ]

    scenario_counter: Counter[str] = Counter()
    for p in papers:
        text = f"{p.title} {p.abstract}".lower()
        for scenario in scenario_keywords:
            if scenario in text:
                scenario_counter[scenario] += 1

    if scenario_counter:
        lines.append("### 应用领域分布")
        lines.append("| 应用领域 | 论文数 |")
        lines.append("|----------|--------|")
        for scenario, count in scenario_counter.most_common(15):
            lines.append(f"| {scenario} | {count} |")
    else:
        lines.append("暂无应用场景数据")
    lines.append("")

    return lines


def _generate_top_papers_section(
    top_papers: List[Tuple[Paper, Dict[str, object] | None]],
) -> List[str]:
    """生成Top论文推荐部分"""
    lines: List[str] = []
    lines.append("## Top论文推荐")
    lines.append("")

    if top_papers:
        lines.append("基于综合评分，以下是推荐的Top论文：")
        lines.append("")
        for idx, (paper, analysis) in enumerate(top_papers[:20], 1):
            lines.append(f"### {idx}. {paper.title}")
            lines.append("")
            if paper.authors:
                lines.append(f"**作者**: {', '.join(paper.authors[:5])}")
                if len(paper.authors) > 5:
                    lines.append(f"等{len(paper.authors)}人")
            lines.append("")
            if paper.venue:
                lines.append(f"**发表平台**: {paper.venue}")
            if paper.year:
                lines.append(f"**年份**: {paper.year}")
            lines.append("")
            if paper.tags:
                lines.append(f"**标签**: {', '.join(paper.tags)}")
            lines.append("")
            if paper.abstract:
                abstract_preview = paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract
                lines.append(f"**摘要**: {abstract_preview}")
            lines.append("")
            if analysis and isinstance(analysis, dict):
                novelty = analysis.get("novelty_score", "")
                if novelty:
                    lines.append(f"**新颖性评分**: {novelty}/5")
            if paper.primaryUrl:
                lines.append(f"**链接**: [{paper.primaryUrl}]({paper.primaryUrl})")
            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("暂无Top论文数据")
    lines.append("")

    return lines


def _generate_research_problems(analyses: List[Dict[str, object]]) -> List[str]:
    """生成研究问题聚类"""
    lines: List[str] = []
    lines.append("## 研究问题聚类")
    lines.append("")

    problems: List[str] = []
    for analysis_item in analyses:
        analysis = analysis_item.get("analysis", {})
        if isinstance(analysis, dict):
            problem = analysis.get("problem", "")
            if problem and isinstance(problem, str):
                problems.append(problem)

    if problems:
        lines.append("基于LLM分析，主要研究问题包括：")
        lines.append("")
        for idx, problem in enumerate(problems[:10], 1):
            lines.append(f"{idx}. {problem}")
            lines.append("")
    else:
        lines.append("暂无研究问题数据")
    lines.append("")

    return lines


def _generate_limitations_future(analyses: List[Dict[str, object]]) -> List[str]:
    """生成局限性与未来方向"""
    lines: List[str] = []
    lines.append("## 局限性与未来方向")
    lines.append("")

    limitations: List[str] = []
    for analysis_item in analyses:
        analysis = analysis_item.get("analysis", {})
        if isinstance(analysis, dict):
            limitation = analysis.get("limitations", "")
            if limitation and isinstance(limitation, str):
                limitations.append(limitation)

    if limitations:
        lines.append("### 当前研究的局限性")
        lines.append("")
        for idx, limitation in enumerate(limitations[:10], 1):
            lines.append(f"{idx}. {limitation}")
            lines.append("")
    else:
        lines.append("暂无局限性数据")
    lines.append("")

    # 未来方向（从limitations中提取）
    future_keywords = [
        "未来", "进一步", "改进", "扩展", "优化", "提升", "增强",
        "future", "improve", "enhance", "extend", "optimize"
    ]

    future_directions: List[str] = []
    for limitation in limitations:
        limitation_lower = limitation.lower()
        if any(kw in limitation_lower for kw in future_keywords):
            future_directions.append(limitation)

    if future_directions:
        lines.append("### 未来研究方向")
        lines.append("")
        for idx, direction in enumerate(future_directions[:5], 1):
            lines.append(f"{idx}. {direction}")
            lines.append("")
    lines.append("")

    return lines


def _generate_author_analysis(
    papers: List[Paper],
    stats: StatsReport,
) -> List[str]:
    """生成作者与机构分析"""
    lines: List[str] = []
    lines.append("## 作者与机构分析")
    lines.append("")

    # 活跃作者
    lines.append("### 活跃作者")
    if stats.top_authors:
        lines.append("| 排名 | 作者 | 论文数 |")
        lines.append("|------|------|--------|")
        for idx, (author, count) in enumerate(stats.top_authors[:15], 1):
            lines.append(f"| {idx} | {author} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    # 合作分析（共同作者）
    coauthor_counter: Counter[Tuple[str, str]] = Counter()
    for p in papers:
        authors_list = sorted(p.authors)
        for i, author1 in enumerate(authors_list):
            for author2 in authors_list[i + 1:]:
                coauthor_counter[(author1, author2)] += 1

    if coauthor_counter:
        lines.append("### 作者合作分析")
        lines.append("以下作者经常合作：")
        lines.append("")
        lines.append("| 作者对 | 合作次数 |")
        lines.append("|--------|----------|")
        for (author1, author2), count in coauthor_counter.most_common(10):
            lines.append(f"| {author1} & {author2} | {count} |")
    lines.append("")

    return lines


def _generate_source_analysis(
    papers: List[Paper],
    advanced_stats: AdvancedStatsReport,
) -> List[str]:
    """生成数据源分析"""
    lines: List[str] = []
    lines.append("## 数据源分析")
    lines.append("")

    # 数据源分布
    lines.append("### 数据源分布")
    if advanced_stats.source_distribution:
        lines.append("| 数据源 | 论文数 |")
        lines.append("|--------|--------|")
        for source, count in advanced_stats.source_distribution:
            lines.append(f"| {source} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    # 发表平台分布
    lines.append("### 发表平台分布")
    if advanced_stats.venue_distribution:
        lines.append("| 平台 | 论文数 |")
        lines.append("|------|--------|")
        for venue, count in advanced_stats.venue_distribution:
            lines.append(f"| {venue} | {count} |")
    else:
        lines.append("暂无数据")
    lines.append("")

    return lines

