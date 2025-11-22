from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
import os

# 确保可以从任意工作目录运行：将当前文件所在的 src 目录加入 sys.path
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
# 同时将仓库根目录加入 sys.path 以便导入顶层 common 模块
_REPO_ROOT = _SRC_DIR.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents_papers.pipeline.fetch import fetch_all_sources
from agents_papers.pipeline.parse import parse_records
from agents_papers.pipeline.normalize import normalize_records
from agents_papers.pipeline.deduplicate import deduplicate_papers
from agents_papers.pipeline.classify import classify_papers
from agents_papers.pipeline.quality_filter import filter_high_quality
from agents_papers.pipeline.summarize import summarize_papers
from agents_papers.pipeline.export import export_all
from agents_papers.utils.dates import ensure_data_dirs
from agents_papers.analysis.statistics import generate_statistics, generate_advanced_statistics
from agents_papers.analysis.llm_analysis import analyze_with_llm
from agents_papers.analysis.selector import select_top_k, rank_papers
from agents_papers.pipeline.download import download_pdfs


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Monthly AI Agent papers ETL")
    parser.add_argument("--month", required=False, help="Month in YYYY-MM format")
    parser.add_argument("--start", required=False, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=False, help="End date YYYY-MM-DD")
    args = parser.parse_args()
    # 若三者均未提供，后续将使用 utils.dates.derive_label 自动推导标签

    # 启用 OpenReview 数据源（也可在外部通过环境变量设置）
    os.environ.setdefault("OPENREVIEW_ENABLED", "1")

    configure_logging()
    logger = logging.getLogger("monthly_run")

    # Derive label and build submittedDate window
    from agents_papers.utils.dates import parse_date, derive_label, format_yyyymmdd
    start_dt = parse_date(args.start) if args.start else None
    end_dt = parse_date(args.end) if args.end else None
    label = derive_label(month=args.month, start=start_dt, end=end_dt)
    dirs = ensure_data_dirs(label)

    submitted_start = format_yyyymmdd(start_dt) if start_dt else None
    submitted_end = format_yyyymmdd(end_dt) if end_dt else None

    logger.info("Fetching raw data for label=%s", label)
    raw_records = fetch_all_sources(
        month=args.month or label,
        output_dir=dirs["raw"],
        submitted_start=submitted_start,
        submitted_end=submitted_end,
    )

    logger.info("Parsing raw records")
    parsed = parse_records(raw_records)

    logger.info("Normalizing to Paper model")
    papers = normalize_records(parsed, month=(args.month or label), start_date=args.start, end_date=args.end)

    logger.info("Deduplicating %d papers", len(papers))
    unique_papers = deduplicate_papers(papers)

    logger.info("Filtering high quality and institution-focused papers")
    high_quality = filter_high_quality(unique_papers, min_score=2, require_institution=True)

    logger.info("Classifying papers")
    classified = classify_papers(high_quality)

    logger.info("Summarizing papers")
    summarized = summarize_papers(classified)

    # Download PDFs
    logger.info("Downloading PDFs for finalized papers")
    pdf_dir = dirs["raw"] / "pdfs"
    download_pdfs(summarized, pdf_dir)

    logger.info("Exporting outputs")
    export_all(summarized, export_dir=dirs["exports"], month=label)
    logger.info("Done. Export directory: %s", str(dirs["exports"]))

    # Statistics
    logger.info("Generating statistics report")
    stats = generate_statistics(summarized)
    from agents_papers.pipeline.export import export_statistics, export_top10
    export_statistics(stats, Path(dirs["exports"]) / f"{label}-stats.json")

    # LLM analysis + Top10 selection
    logger.info("Running LLM analysis and selecting Top10")
    analyses = analyze_with_llm(summarized, budget=20)
    top10 = select_top_k(summarized, analyses, k=50)
    export_top10(top10, Path(dirs["exports"]) / f"{label}-top10.json")
    ranked = rank_papers(summarized, analyses)
    from agents_papers.pipeline.export import export_ranked_rest, export_stats_md_cn, export_comprehensive_report
    export_ranked_rest(
        ranked,
        path_all=Path(dirs["exports"]) / f"{label}-ranked-all.json",
        path_rest=Path(dirs["exports"]) / f"{label}-ranked-rest.json",
        top_k=50,
    )
    export_stats_md_cn(stats, Path(dirs["exports"]) / f"{label}-stats-cn.md")

    # Advanced statistics and comprehensive report
    logger.info("Generating advanced statistics")
    advanced_stats = generate_advanced_statistics(summarized)
    logger.info("Generating comprehensive analysis report")
    export_comprehensive_report(
        papers=summarized,
        stats=stats,
        advanced_stats=advanced_stats,
        analyses=analyses,
        ranked_papers=ranked,
        top_papers=top10,
        label=label,
        path=Path(dirs["exports"]) / f"{label}-comprehensive-report.md",
    )
    logger.info("Comprehensive report generated: %s", str(Path(dirs["exports"]) / f"{label}-comprehensive-report.md"))


if __name__ == "__main__":
    os.environ.setdefault('OPENREVIEW_VENUE_ID', 'ICLR.cc/2025/Conference')
    os.environ.setdefault('OPENREVIEW_ENABLED', "0")
    main()


