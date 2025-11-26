"""博客分析报告主入口"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# 路径引导 - 确保可以从项目根目录或 get_blog_posts 目录运行
_current_file = Path(__file__).resolve()
_get_blog_posts_dir = _current_file.parent.parent.parent  # get_blog_posts/
_project_root = _get_blog_posts_dir.parent  # 项目根目录

# 添加项目根目录到路径（用于导入 common 模块）
_project_root_resolved = _project_root.resolve()
if str(_project_root_resolved) not in sys.path:
    sys.path.insert(0, str(_project_root_resolved))

# 添加 get_blog_posts 目录到路径
if str(_get_blog_posts_dir.resolve()) not in sys.path:
    sys.path.insert(0, str(_get_blog_posts_dir.resolve()))

from src.analysis.reader import read_blog_posts
from src.analysis.report_writer import write_report
from config import get_output_dir

# 使用统一的配置加载器
from common.config_loader import get_env, load_env_config

# 确保加载 .env 文件
load_env_config()


logger = logging.getLogger("blog_analysis")


def setup_logging(level: str) -> None:
    """配置日志"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "blog_analysis.log"
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"日期格式错误，应为 YYYY-MM-DD: {date_str}")


def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description="博客内容分析报告生成器")
    parser.add_argument(
        "--exports-dir",
        type=str,
        default=str(Path(get_output_dir())),
        help="博客导出目录（默认: data/exports）",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="开始日期 YYYY-MM-DD（可选）",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="结束日期 YYYY-MM-DD（可选）",
    )
    parser.add_argument(
        "--last-days",
        type=int,
        help="最近 N 天（与 --start/--end 互斥）",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="筛选特定来源（如 langchain, anthropic）",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径（默认: reports/blog-analysis-<timestamp>.md）",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认: INFO）",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="禁用 LLM 分析（使用模板化分析）",
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    try:
        # 确定时间范围
        start_dt: Optional[datetime] = None
        end_dt: Optional[datetime] = None
        
        if args.start and args.end:
            start_dt = parse_date(args.start)
            end_dt = parse_date(args.end)
            # 结束日期包含整天
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        elif args.last_days:
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(days=args.last_days)
            start_dt = start_dt.replace(hour=0, minute=0, second=0)
        elif args.start:
            start_dt = parse_date(args.start)
            end_dt = datetime.now(timezone.utc)
        elif args.end:
            end_dt = parse_date(args.end)
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        
        # 确定输出路径
        if args.output:
            output_path = Path(args.output)
        else:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = reports_dir / f"blog-analysis-{timestamp}.md"
        
        # 读取博客文章
        exports_dir = Path(args.exports_dir)
        logger.info("开始读取博客文章，目录: %s", exports_dir)
        
        items = read_blog_posts(
            exports_root=exports_dir,
            start_dt=start_dt,
            end_dt=end_dt,
            source_filter=args.source,
            logger=logger,
        )
        
        if not items:
            logger.warning("未找到任何博客文章")
            return 1
        
        logger.info("读取到 %d 篇博客文章", len(items))
        
        # 确定是否使用 LLM
        use_llm = not args.no_llm and bool(get_env("LLM_API_KEY"))
        if use_llm:
            logger.info("启用 LLM 深度分析")
        else:
            logger.info("使用模板化分析")
        
        # 生成报告
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_report(
            path=output_path,
            items=items,
            start_dt=start_dt,
            end_dt=end_dt,
            use_llm=use_llm,
            logger=logger,
        )
        
        logger.info("报告生成完成: %s", output_path)
        return 0
        
    except Exception as exc:
        logger.exception("生成报告失败: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

