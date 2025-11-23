"""报告生成主入口"""

from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from .image_generator import generate_images_and_insert, judge_image_generation
from .models import NewsAggItem, PaperItem, ReleaseAggItem
from .readers import read_news, read_papers, read_releases
from .report_writer import write_report
from .runners import run_get_agent_news, run_get_paper, run_sdk_release_change_log
from .stats import aggregate_daily_counts
from .utils import (
    derive_label,
    derive_range,
    ensure_dir,
    setup_logging,
)


def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description="Weekly/Range Intelligence Report Orchestrator")
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--last-days", type=int, default=7, help="Use last N days when start/end not provided")
    parser.add_argument("--paper-root", default=str(Path("get_paper") / "data"), help="get_paper data root")
    parser.add_argument("--news-root", default=str(Path("get_agent_news") / "data" / "exports"), help="get_agent_news exports root")
    parser.add_argument("--sdk-root", default=str(Path("get_sdk_release_change_log") / "data"), help="sdk release change log data root")
    parser.add_argument("--repos", default="", help="Comma separated repo list filter for SDK, e.g. org1/repo1,org2/repo2")
    parser.add_argument("--output-root", default="reports", help="Output root directory")
    parser.add_argument("--overwrite", default=True, action="store_true", help="Overwrite existing report if present")
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"), help="Log level")
    # Run-sources mode（默认启用执行子工程，提供 --no-run-sources 关闭）
    parser.add_argument("--no-run-sources", action="store_true", help="Do NOT trigger sub-projects; only aggregate existing outputs")
    parser.add_argument("--news-since-days", type=int, default=7, help="When running get_agent_news, use this window")
    parser.add_argument("--sdk-start-page", type=int, default=1, help="SDK releases: start page")
    parser.add_argument("--sdk-max-pages", type=int, default=2, help="SDK releases: max pages to fetch")
    parser.add_argument("--name-by-exec-time", action="store_true", help="Name output directory by execution time prefix")
    parser.add_argument("--enable-image-generation", default=True, action="store_true", help="Enable automatic image generation for the report")
    args = parser.parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger("weekly_report")
    try:
        start_dt, end_dt = derive_range(args.start, args.end, args.last_days)
        label = derive_label(start_dt, end_dt)

        paper_root = Path(args.paper_root)
        news_root = Path(args.news_root)
        sdk_root = Path(args.sdk_root)
        output_root = Path(args.output_root)
        exec_prefix = ""
        execution_timeline: List[Tuple[str, datetime]] = []
        run_sources = not args.no_run_sources
        if run_sources:
            # Run in sequence and record timestamps
            ts1 = datetime.now(timezone.utc)
            run_get_paper(start_dt, end_dt, logger)
            execution_timeline.append(("get_paper", ts1))

            ts2 = datetime.now(timezone.utc)
            run_get_agent_news(args.news_since_days, logger)
            execution_timeline.append(("get_agent_news", ts2))

            repos_list = [s.strip() for s in (args.repos.split(",") if args.repos else []) if s.strip()]
            if repos_list:
                ts3 = datetime.now(timezone.utc)
                run_sdk_release_change_log(repos_list, args.sdk_start_page, args.sdk_max_pages, logger)
                execution_timeline.append(("get_sdk_release_change_log", ts3))
            # when run-sources, default to prefix with exec time
            exec_prefix = datetime.now().strftime("%Y%m%d_%H%M%S") + "-"
        if args.name_by_exec_time and not exec_prefix:
            exec_prefix = datetime.now().strftime("%Y%m%d_%H%M%S") + "-"

        out_dir = output_root / f"{exec_prefix}{label}"
        ensure_dir(out_dir)
        out_path = out_dir / "weekly-intel-report.md"
        if out_path.exists() and out_path.stat().st_size > 0 and not args.overwrite:
            logger.info("报告已存在且非空，跳过写入（使用 --overwrite 可覆盖）：%s", str(out_path))
            return 0

        # Read sources
        papers = read_papers(paper_root, label, logger, start_dt=start_dt, end_dt=end_dt)
        news = read_news(news_root, start_dt, end_dt, logger)
        repos_filter = [s.strip() for s in args.repos.split(",") if s.strip()] if args.repos else None
        releases = read_releases(sdk_root, start_dt, end_dt, repos_filter, logger)

        daily_counts = aggregate_daily_counts(papers, news, releases, start_dt, end_dt)

        # 使用统一的配置加载器
        from common.config_loader import get_env, load_env_config
        load_env_config()
        use_llm = bool(get_env("LLM_API_KEY"))
        
        # 图片生成逻辑
        position_to_image: Dict[str, str] = {}
        if args.enable_image_generation:
            logger.info("图片生成功能已启用")
            # 判断需要生成哪些图片
            image_requests = judge_image_generation(papers, news, releases, daily_counts, logger)
            logger.info("图片判断结果: 共 %d 个图片请求", len(image_requests))
            if image_requests:
                # 生成图片
                position_to_image = generate_images_and_insert(out_dir, image_requests, logger)
                logger.info("图片生成结果: 共生成 %d 张图片", len(position_to_image))
            else:
                logger.info("未找到适合生成图片的内容")
        else:
            logger.info("图片生成功能未启用（使用 --enable-image-generation 启用）")
        
        write_report(
            path=out_path,
            label=label,
            start_dt=start_dt,
            end_dt=end_dt,
            papers=papers,
            news=news,
            releases=releases,
            daily_counts=daily_counts,
            use_llm=use_llm,
            logger=logger,
            execution_timeline=execution_timeline if run_sources else None,
            enable_image_generation=args.enable_image_generation,
            position_to_image=position_to_image if position_to_image else None,
        )
        return 0
    except Exception as exc:
        logger.exception("生成报告失败: %s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
