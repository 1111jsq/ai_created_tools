from __future__ import annotations

# 兼容直接运行 src/main.py 的路径引导
# 确保可以从项目根目录或 get_agent_news 目录运行
import os as _os
import sys as _sys
from pathlib import Path

# 如果作为模块运行（python -m src.main），__package__ 不为 None
# 如果直接运行（python src/main.py），__package__ 为 None
if __package__ is None or __package__ == "":
    # 直接运行模式：添加 get_agent_news 目录到路径
    _current_file = Path(__file__).resolve()
    _get_agent_news_dir = _current_file.parent.parent
    if str(_get_agent_news_dir) not in _sys.path:
        _sys.path.insert(0, str(_get_agent_news_dir))
    
    # 同时添加项目根目录，以便导入 common 模块
    _project_root = _get_agent_news_dir.parent
    if str(_project_root) not in _sys.path:
        _sys.path.insert(0, str(_project_root))

import argparse
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import yaml

from src.models import NewsItem
from src.pipelines.normalize import normalize_items
from src.pipelines.deduplicate import deduplicate_items, get_deduplication_stats
from src.sources.rss_adapter import fetch_rss
from src.sources.web_adapter import fetch_web
from src.sources.wechat_adapter import fetch_wechat_search
from src.sources.aibase_daily import export_aibase_daily
from src.storage.file_storage import save_items_to_directory, FileStorage
from src.config import get_sources_path, get_log_path
from src.pipelines.markdown_export import export_news_items_by_date
from src.pipelines.markdown_index import build_index


logger = logging.getLogger("main")


def setup_logging(level: str) -> None:
    os.makedirs(os.path.dirname(get_log_path()), exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(get_log_path(), encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_sources(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def iter_items_from_sources(sources_cfg: Dict[str, Any], since_days: int, web_since_days: Optional[int] = None) -> Iterable[NewsItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    web_cutoff = datetime.now(timezone.utc) - timedelta(days=web_since_days if web_since_days is not None else since_days)

    rss_list = (sources_cfg.get("rss", []) or [])
    web_list = (sources_cfg.get("web", []) or [])
    wechat_list = (sources_cfg.get("wechat", []) or [])
    daily_list = (sources_cfg.get("daily", []) or [])

    enabled_rss = [s for s in rss_list if s.get("enabled", True)]
    enabled_web = [s for s in web_list if s.get("enabled", True)]
    enabled_wechat = [s for s in wechat_list if s.get("enabled", True)]
    enabled_daily = [s for s in daily_list if s.get("enabled", True)]
    logger.info(
        "来源统计: rss(total=%s, enabled=%s), web(total=%s, enabled=%s), wechat(total=%s, enabled=%s)",
        len(rss_list), len(enabled_rss), len(web_list), len(enabled_web), len(wechat_list), len(enabled_wechat)
    )

    # RSS
    for rss_entry in enabled_rss:
        name = rss_entry.get("name")
        url = rss_entry.get("url")
        tags = rss_entry.get("tags", [])
        try:
            raw_items = list(fetch_rss(name, url, tags))
        except Exception as e:
            logger.exception("RSS 抓取失败: name=%s url=%s err=%s", name, url, e)
            continue
        kept = [i for i in raw_items if not i.published_at or i.published_at >= cutoff]
        logger.info(
            "RSS 完成: name=%s url=%s raw=%s kept=%s cutoff=%s",
            name, url, len(raw_items), len(kept), cutoff.isoformat()
        )
        for item in kept:
            yield item

    # Web
    for web_entry in enabled_web:
        name = web_entry.get("name")
        url = web_entry.get("url")
        tags = web_entry.get("tags", [])
        selector = (web_entry.get("selector") or {})
        filters = (web_entry.get("filters") or {})
        pagination = (web_entry.get("pagination") or {})
        include_keywords = filters.get("include_keywords", [])
        if not selector or not selector.get("item"):
            logger.warning("Web 来源缺少 selector.item: name=%s url=%s", name, url)
            continue
        try:
            logger.info(
                "Web 调用配置: name=%s selector.item=%s url_attr=%s title_attr=%s pagination=%s include_keywords=%s",
                name,
                selector.get("item"),
                selector.get("url_attr", "href"),
                selector.get("title_attr", "text"),
                pagination or {},
                include_keywords,
            )
            raw_items = list(
                fetch_web(
                    name=name,
                    url=url,
                    selector_item=selector.get("item"),
                    url_attr=selector.get("url_attr", "href"),
                    title_attr=selector.get("title_attr", "text"),
                    include_keywords=include_keywords,
                    tags=tags,
                    pagination=pagination,
                )
            )
        except Exception as e:
            logger.exception("Web 抓取失败: name=%s url=%s err=%s", name, url, e)
            continue
        kept = [i for i in raw_items if i.fetched_at >= web_cutoff]
        logger.info(
            "Web 完成: name=%s url=%s raw=%s kept=%s cutoff(web)=%s",
            name, url, len(raw_items), len(kept), web_cutoff.isoformat()
        )
        for item in kept:
            yield item

    # WeChat (via Sogou search)
    for w_entry in enabled_wechat:
        name = w_entry.get("name")
        query = w_entry.get("query")
        tags = w_entry.get("tags", [])
        max_pages = int(w_entry.get("max_pages", 1))
        if not query:
            logger.warning("WeChat 来源缺少 query: name=%s", name)
            continue
        try:
            raw_items = list(fetch_wechat_search(name=name, query=query, tags=tags, max_pages=max_pages))
        except Exception as e:
            logger.exception("WeChat 抓取失败: name=%s query=%s err=%s", name, query, e)
            continue
        kept = [i for i in raw_items if i.fetched_at >= web_cutoff]
        logger.info(
            "WeChat 完成: name=%s query=%s raw=%s kept=%s cutoff(web)=%s",
            name, query, len(raw_items), len(kept), web_cutoff.isoformat()
        )
        for item in kept:
            yield item

    # AIbase Daily 导出移动至 main 中按 CLI 控制执行


def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly AI Agent/LLM news fetcher")
    parser.add_argument("--once", action="store_true", help="单次运行一次抓取流程")
    parser.add_argument("--since-days", type=int, default=15, help="仅抓取 N 天内更新（RSS 等通用）")
    parser.add_argument("--news-since-days", type=int, default=2, help="资讯回溯天数（Web/WeChat）")
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"), help="日志级别")
    parser.add_argument("--export-dir", default=os.path.join("data", "exports"), help="结构化导出根目录（CSV/JSON）")
    parser.add_argument("--source", choices=["daily", "news", "all"], default="daily", help="选择抓取来源类型")
    parser.add_argument("--export-markdown", action="store_true", help="将抓取结果导出为 Markdown 到 content/")
    parser.add_argument("--stop-on-duplicate-daily", action="store_true", default=True, help="日报遇重复即停止分页")
    parser.add_argument("--max-pages-daily", type=int, default=0, help="日报抓取最大页数（0 表示按配置）")
    args = parser.parse_args()

    setup_logging(args.log_level)

    try:
        sources_path = get_sources_path()
        logger.info("加载来源配置: %s", sources_path)
        sources = load_sources(sources_path)
    except FileNotFoundError:
        logger.error("未找到 sources.yaml: %s", get_sources_path())
        return 2

    # 创建本次运行目录（用于保存导出数据）
    run_time = datetime.now()
    run_dir_name = run_time.strftime("%Y%m%d_%H%M%S")

    try:
        # 初始化文件系统存储
        file_storage = FileStorage()

        # 内容根目录（Markdown）
        content_root = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), "content")
        if args.export_markdown:
            os.makedirs(content_root, exist_ok=True)

        # 处理日报（daily）
        new_daily_written = 0
        if args.source in ("daily", "all"):
            daily_list = (sources.get("daily", []) or [])
            enabled_daily = [s for s in daily_list if s.get("enabled", True)]
            for d_entry in enabled_daily:
                name = d_entry.get("name")
                url = d_entry.get("url")
                max_pages_cfg = int(d_entry.get("max_pages", 3))
                api_cfg = d_entry.get("api")
                max_pages = args.max_pages_daily if args.max_pages_daily > 0 else max_pages_cfg
                try:
                    logger.info("AIbase 日报导出: name=%s url=%s max_pages=%s api=%s", name, url, max_pages, bool(api_cfg))
                    written = export_aibase_daily(
                        url,
                        output_dir=content_root,
                        max_pages=max_pages,
                        api_config=api_cfg,
                        stop_on_duplicate=args.stop_on_duplicate_daily,
                        # storage=storage, # Removed SQLiteStorage
                    )
                    new_daily_written += len(written)
                    logger.info("AIbase 日报导出完成: name=%s written=%s", name, len(written))
                except Exception as e:
                    logger.exception("AIbase 日报导出失败: name=%s url=%s err=%s", name, url, e)

        # 处理资讯（news）
        items: List[NewsItem] = []
        new_news_written = 0
        if args.source in ("news", "all"):
            items = list(iter_items_from_sources(sources, since_days=args.since_days, web_since_days=args.news_since_days))
            if not items:
                logger.warning("未获取到任何候选项，请检查网络、代理、sources.yaml 或选择器/关键词设置。")
            else:
                logger.info("候选项数量: %s", len(items))
            items = normalize_items(items)
            items = deduplicate_items(items)
            export_path = save_items_to_directory(items, base_dir=args.export_dir, run_time=run_time)
            logger.info("已保存到目录: %s", export_path)

            # 可选：资讯 Markdown（按日期分组）
            if args.export_markdown and items:
                try:
                    exported_paths = export_news_items_by_date(items, base_dir=content_root)
                    new_news_written = len(exported_paths)
                    logger.info("已导出 %s 个日期的资讯文件", new_news_written)
                except Exception:
                    logger.exception("导出资讯 Markdown 失败")

        # 目录页
        if args.export_markdown:
            index_path = build_index(
                content_root=content_root,
                new_daily=new_daily_written,
                new_news=new_news_written,
                params={
                    "since_days": str(args.since_days),
                    "news_since_days": str(args.news_since_days),
                    "source": args.source,
                },
            )
            logger.info("目录页生成: %s", index_path)
    except Exception as exc:
        logger.exception("抓取流程失败: %s", exc)
        return 2

    # 对于仅日报场景，items 可能为空
    logger.info("完成：saved=%s", len(items) if isinstance(items, list) else 0)
    
    # 输出存储统计
    storage_stats = file_storage.get_storage_stats()
    logger.info("存储统计: %s", storage_stats)
    
    # 输出去重统计
    dedup_stats = get_deduplication_stats()
    logger.info("去重统计: %s", dedup_stats)
    
    return 0


if __name__ == "__main__":
    # 代理配置应从环境变量读取，不在此硬编码
    # 如果需要在代码中设置默认值，应通过 common/config_loader 统一管理
    raise SystemExit(main())


#我会先打开并修复 `src/main.py` 中缩进混用（Tab 与空格）的行，把相关参数定义区块统一为与文件一致的缩进风格，然后再次检查是否还有类似问题。
# - 示例：仅日报（遇重复即停）
#   - uv run python -m src.main --once --source daily --export-markdown --stop-on-duplicate-daily
# - 示例：仅资讯（回溯 7 天）
#   - uv run python -m src.main --once --source news --news-since-days 7 --export-markdown
# - 同时抓取
#   - uv run python -m src.main --once --source all --news-since-days 7 --export-markdown --stop-on-duplicate-daily
