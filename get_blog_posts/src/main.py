"""CLI 入口"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

# 路径引导 - 确保可以从项目根目录或 get_blog_posts 目录运行
_current_file = Path(__file__).resolve()
_get_blog_posts_dir = _current_file.parent.parent  # get_blog_posts/
_project_root = _get_blog_posts_dir.parent  # 项目根目录

# 添加项目根目录到路径（用于导入 common 模块）
_project_root_resolved = _project_root.resolve()
if str(_project_root_resolved) not in sys.path:
    sys.path.insert(0, str(_project_root_resolved))

# 添加 get_blog_posts 目录到路径（用于导入 src 模块和 config）
if str(_get_blog_posts_dir.resolve()) not in sys.path:
    sys.path.insert(0, str(_get_blog_posts_dir.resolve()))

from src.crawler import BlogCrawler
from src.models import BlogPost, compute_url_hash
from src.parsers.html_parser import fetch_single_url
from src.storage.file_storage import save_posts_to_directory
from config import get_config_path, get_output_dir, get_log_path


logger = logging.getLogger("main")


def setup_logging(level: str) -> None:
    """配置日志"""
    log_path = get_log_path()
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_config(config_path: Path) -> Dict:
    """加载配置文件"""
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if not config or "blogs" not in config:
        raise ValueError("配置文件格式错误：缺少 'blogs' 字段")
    
    return config


def get_existing_url_hashes(output_dir: Path) -> Set[str]:
    """获取已存在的文章 URL hash（用于去重）"""
    url_hashes = set()
    
    # 遍历所有导出目录
    for run_dir in output_dir.iterdir():
        if not run_dir.is_dir():
            continue
        
        markdown_dir = run_dir / "markdown"
        if not markdown_dir.exists():
            continue
        
        # 遍历所有 Markdown 文件
        for md_file in markdown_dir.rglob("*.md"):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 从元数据中提取 URL（简单实现）
                    if "**URL**: " in content:
                        url_line = [line for line in content.split("\n") if "**URL**: " in line]
                        if url_line:
                            url = url_line[0].split("**URL**: ")[1].strip()
                            url_hashes.add(compute_url_hash(url))
            except Exception:
                pass
    
    return url_hashes


def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description="博客文章爬虫")
    parser.add_argument(
        "--config",
        type=str,
        default=str(get_config_path()),
        help="配置文件路径（默认: configs/blogs.yaml）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(get_output_dir()),
        help="输出目录（默认: data/exports）",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="指定单个博客源名称",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="覆盖配置中的 max_pages",
    )
    parser.add_argument(
        "--delay",
        type=float,
        help="覆盖配置中的 delay（秒）",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的文章",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认: INFO）",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="抓取单个 URL（直接指定要抓取的网页 URL）",
    )
    parser.add_argument(
        "--url-source",
        type=str,
        dest="url_source",
        help="当使用 --url 时，指定来源名称（默认从 URL 提取域名）",
    )
    parser.add_argument(
        "--url-tags",
        type=str,
        nargs="+",
        dest="url_tags",
        help="当使用 --url 时，指定标签列表（默认从 URL 提取域名）",
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    try:
        output_dir = Path(args.output_dir)
        
        # 如果指定了 --url，直接抓取单个 URL
        if args.url:
            logger.info("使用单 URL 模式抓取: %s", args.url)
            
            # 检查是否已存在
            existing_url_hashes = get_existing_url_hashes(output_dir) if not args.overwrite else set()
            url_hash = compute_url_hash(args.url)
            if url_hash in existing_url_hashes and not args.overwrite:
                logger.info("文章已存在，跳过: %s", args.url)
                return 0
            
            # 抓取单 URL
            post = fetch_single_url(
                url=args.url,
                source=getattr(args, 'url_source', None),
                tags=getattr(args, 'url_tags', None),
                timeout=30.0,
            )
            
            if not post:
                logger.error("抓取失败: %s", args.url)
                return 1
            
            # 保存文章
            logger.info("开始保存文章: %s", post.title)
            export_path = save_posts_to_directory(
                posts=[post],
                base_dir=str(output_dir),
                run_time=datetime.now(),
                overwrite=args.overwrite,
            )
            logger.info("文章已保存到: %s", export_path)
            return 0
        
        # 否则使用配置文件模式
        # 加载配置
        config_path = Path(args.config)
        logger.info("加载配置文件: %s", config_path)
        config_data = load_config(config_path)
        
        # 获取已存在的 URL hash（用于去重）
        existing_url_hashes = get_existing_url_hashes(output_dir) if not args.overwrite else set()
        logger.info("已存在文章数量: %s", len(existing_url_hashes))
        
        # 筛选博客源
        blogs = config_data["blogs"]
        if args.source:
            blogs = [b for b in blogs if b.get("name") == args.source]
            if not blogs:
                logger.error("未找到指定的博客源: %s", args.source)
                return 1
        
        # 爬取每个博客源
        all_posts: List[BlogPost] = []
        for blog_config in blogs:
            blog_name = blog_config.get("name", "unknown")
            blog_url = blog_config.get("url", "")
            
            if not blog_url:
                logger.warning("博客源 %s 缺少 URL，跳过", blog_name)
                continue
            
            # 覆盖配置参数
            if args.max_pages and "pagination" in blog_config:
                blog_config["pagination"]["max_pages"] = args.max_pages
            if args.delay is not None:
                blog_config["delay"] = args.delay
            
            try:
                crawler = BlogCrawler(
                    source=blog_name,
                    url=blog_url,
                    config=blog_config,
                    existing_url_hashes=existing_url_hashes,
                )
                posts = crawler.crawl()
                all_posts.extend(posts)
                logger.info("博客源 %s 抓取完成，共 %s 篇文章", blog_name, len(posts))
            except Exception as exc:
                logger.exception("博客源 %s 抓取失败: %s", blog_name, exc)
                continue
        
        # 保存文章
        if all_posts:
            logger.info("开始保存文章，共 %s 篇", len(all_posts))
            export_path = save_posts_to_directory(
                posts=all_posts,
                base_dir=str(output_dir),
                run_time=datetime.now(),
                overwrite=args.overwrite,
            )
            logger.info("文章已保存到: %s", export_path)
        else:
            logger.warning("未抓取到任何文章")
        
        return 0
        
    except Exception as exc:
        logger.exception("程序执行失败: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

