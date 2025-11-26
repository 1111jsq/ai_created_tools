from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, Dict, Any, Optional

from src.models import NewsItem
from src.tools.date_structure import ensure_date_structure
from src.storage.file_stats import FileStatsCollector


class FileStorage:
    """文件系统存储管理器"""
    
    def __init__(self, base_dir: str = "content", date_format: str = "%Y/%m/%d"):
        self.base_dir = base_dir
        self.date_format = date_format
        self.stats_collector = FileStatsCollector()
    
    def save_news_items_by_date(self, items: List[NewsItem], sub_dir: str = "news") -> List[str]:
        """按日期批量保存新闻项到文件系统，同一天的新闻合并到一个文件中
        
        Args:
            items: 新闻项列表
            sub_dir: 子目录名称
            
        Returns:
            保存的文件路径列表
        """
        if not items:
            return []
        
        # 按日期分组
        items_by_date = defaultdict(list)
        for item in items:
            date_obj = (item.published_at or item.fetched_at).date()
            items_by_date[date_obj].append(item)
        
        exported_paths = []
        for date_obj, date_items in items_by_date.items():
            # 创建日期分层目录
            date_dir = ensure_date_structure(
                os.path.join(self.base_dir, sub_dir),
                datetime.combine(date_obj, datetime.min.time()),
                self.date_format
            )
            
            # 文件名：YYYY-MM-DD.md
            filename = f"{date_obj.isoformat()}.md"
            file_path = os.path.join(date_dir, filename)
            
            # 生成Markdown内容
            lines = [f"# {date_obj.isoformat()} 资讯", ""]
            
            for idx, item in enumerate(date_items, 1):
                lines.append(self._generate_markdown(item))
                if idx < len(date_items):
                    lines.append("---")
                    lines.append("")
            
            content = "\n".join(lines)
            
            # 写入文件（覆盖模式）
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 记录统计
            self.stats_collector.record_file_write(
                file_path, len(content.encode('utf-8')), 0
            )
            
            exported_paths.append(file_path)
        
        return exported_paths
    
    def save_news_item(self, item: NewsItem, sub_dir: str = "news") -> str:
        """保存单个新闻项到文件系统（已废弃，保留用于兼容性）
        
        Args:
            item: 新闻项
            sub_dir: 子目录名称
            
        Returns:
            保存的文件路径
        """
        return self.save_news_items_by_date([item], sub_dir)[0]
    
    def _generate_markdown(self, item: NewsItem) -> str:
        """生成单个新闻项的Markdown内容"""
        lines = []
        lines.append(f"## {item.title}")
        lines.append("")
        
        if item.published_at:
            lines.append(f"**发布时间**: {item.published_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        lines.append(f"**来源**: {item.source}")
        lines.append(f"**类型**: {item.source_type}")
        
        if item.tags:
            lines.append(f"**标签**: {', '.join(item.tags)}")
        
        lines.append(f"**抓取时间**: {item.fetched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        
        lines.append(f"**原文链接**: [{item.url}]({item.url})")
        lines.append("")
        
        if item.summary:
            lines.append("### 摘要")
            lines.append("")
            lines.append(item.summary)
            lines.append("")
        
        return "\n".join(lines)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return self.stats_collector.get_summary()


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _serialize_item(item: NewsItem) -> Dict[str, Any]:
    return {
        "source": item.source,
        "title": item.title,
        "url": item.url,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "summary": item.summary,
        "tags": item.tags,
        "source_type": item.source_type,
        "fetched_at": item.fetched_at.isoformat(),
        "url_hash": item.url_hash,
    }


def save_items_to_directory(
    items: Iterable[NewsItem],
    base_dir: str = os.path.join("data", "exports"),
    run_time: Optional[datetime] = None,
) -> str:
    run_time = run_time or datetime.now()
    run_dir_name = run_time.strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, run_dir_name)
    _ensure_dir(run_dir)

    items_list: List[Dict[str, Any]] = [_serialize_item(i) for i in items]

    # JSONL格式导出
    jsonl_path = os.path.join(run_dir, "news.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in items_list:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # CSV格式导出
    csv_path = os.path.join(run_dir, "news.csv")
    fieldnames = [
        "source",
        "title",
        "url",
        "published_at",
        "summary",
        "tags",
        "source_type",
        "fetched_at",
        "url_hash",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in items_list:
            row_out = row.copy()
            row_out["tags"] = ",".join(row_out.get("tags") or [])
            writer.writerow(row_out)

    # Markdown格式导出（按日期分组）
    markdown_dir = os.path.join(run_dir, "markdown")
    _ensure_dir(markdown_dir)
    storage = FileStorage(base_dir=markdown_dir)
    items_list_for_md = list(items)
    if items_list_for_md:
        try:
            storage.save_news_items_by_date(items_list_for_md, "news")
        except Exception:
            pass  # 忽略批量文件写入失败

    # 简单README
    readme_path = os.path.join(run_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            f"run_time: {run_time.isoformat()}\n"
            f"total_items: {len(items_list)}\n"
            f"files: news.jsonl, news.csv, markdown/\n"
        )

    return run_dir
