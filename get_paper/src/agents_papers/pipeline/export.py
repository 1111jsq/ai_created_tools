from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from agents_papers.analysis.report_generator import generate_comprehensive_report
from agents_papers.analysis.statistics import AdvancedStatsReport, StatsReport
from agents_papers.models.paper import Paper


def export_json(papers: List[Paper], path: Path) -> None:
    data = [p.model_dump(mode="json") for p in papers]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def export_csv(papers: List[Paper], path: Path) -> None:
    fieldnames = [
        "paperId",
        "title",
        "authors",
        "venue",
        "year",
        "month",
        "primaryUrl",
        "pdfUrl",
        "tags",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in papers:
            writer.writerow(
                {
                    "paperId": p.paperId,
                    "title": p.title,
                    "authors": ", ".join(p.authors),
                    "venue": p.venue or "",
                    "year": p.year or "",
                    "month": p.month or "",
                    "primaryUrl": p.primaryUrl or "",
                    "pdfUrl": p.pdfUrl or "",
                    "tags": ",".join(p.tags),
                }
            )


def export_md(papers: List[Paper], path: Path) -> None:
    lines: List[str] = []
    lines.append("# AI Agent Papers")
    for p in papers:
        title_line = p.title
        if p.primaryUrl:
            title_line = f"[{p.title}]({p.primaryUrl})"
        lines.append(f"- {title_line}")
        if p.authors:
            lines.append(f"  - Authors: {', '.join(p.authors)}")
        if p.abstract:
            lines.append(f"  - Abstract: {p.abstract}")
        if p.tags:
            lines.append(f"  - Tags: {', '.join(p.tags)}")
        if p.pdfUrl:
            lines.append(f"  - PDF: {p.pdfUrl}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_all(papers: List[Paper], export_dir: Path, month: str) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    export_json(papers, export_dir / f"{month}-agents-papers.json")
    export_csv(papers, export_dir / f"{month}-agents-papers.csv")
    export_md(papers, export_dir / f"{month}-agents-papers.md")


def export_statistics(stats_report, path: Path) -> None:
    payload = {
        "total": stats_report.total,
        "top_authors": stats_report.top_authors,
        "top_tags": stats_report.top_tags,
        "topics_distribution": stats_report.topics_distribution,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_top10(top10, path: Path) -> None:
    # top10: List[Tuple[Paper, Dict]]
    out = []
    for p, analysis in top10:
        out.append(
            {
                "paperId": p.paperId,
                "title": p.title,
                "authors": p.authors,
                "venue": p.venue,
                "year": p.year,
                "month": p.month,
                "primaryUrl": p.primaryUrl,
                "pdfUrl": p.pdfUrl,
                "tags": p.tags,
                "analysis": analysis or {},
            }
        )
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def export_ranked_rest(ranked, path_all: Path, path_rest: Path, top_k: int = 10) -> None:
    # ranked: List[Tuple[Paper, Dict, float]]
    all_out = []
    rest_out = []
    for idx, (p, analysis, score) in enumerate(ranked, start=1):
        row = {
            "rank": idx,
            "score": score,
            "paperId": p.paperId,
            "title": p.title,
            "authors": p.authors,
            "venue": p.venue,
            "year": p.year,
            "month": p.month,
            "primaryUrl": p.primaryUrl,
            "pdfUrl": p.pdfUrl,
            "tags": p.tags,
            "analysis": analysis or {},
        }
        all_out.append(row)
        if idx > top_k:
            rest_out.append(row)
    path_all.write_text(json.dumps(all_out, ensure_ascii=False, indent=2), encoding="utf-8")
    path_rest.write_text(json.dumps(rest_out, ensure_ascii=False, indent=2), encoding="utf-8")


def export_stats_md_cn(stats_report, path: Path) -> None:
    lines: List[str] = []
    lines.append("# 论文统计报告")
    lines.append(f"- 总论文数: {stats_report.total}")
    lines.append("- 作者 TOP10:")
    for name, cnt in stats_report.top_authors:
        lines.append(f"  - {name}: {cnt}")
    lines.append("- 标签 TOP10:")
    for tag, cnt in stats_report.top_tags:
        lines.append(f"  - {tag}: {cnt}")
    lines.append("- 主题分布:")
    for topic, cnt in stats_report.topics_distribution:
        lines.append(f"  - {topic}: {cnt}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_comprehensive_report(
    papers: List[Paper],
    stats: StatsReport,
    advanced_stats: AdvancedStatsReport,
    analyses: List[Dict[str, object]],
    ranked_papers: List[Tuple[Paper, Dict[str, object] | None, float]],
    top_papers: List[Tuple[Paper, Dict[str, object] | None]],
    label: str,
    path: Path,
) -> None:
    """导出全面的智能体分析报告"""
    report_content = generate_comprehensive_report(
        papers=papers,
        stats=stats,
        advanced_stats=advanced_stats,
        analyses=analyses,
        ranked_papers=ranked_papers,
        top_papers=top_papers,
        label=label,
    )
    path.write_text(report_content, encoding="utf-8")


