from __future__ import annotations

import csv
import json
import os
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
    
    def save_news_item(self, item: NewsItem, sub_dir: str = "news") -> str:
        """保存新闻项到文件系统
        
        Args:
            item: 新闻项
            sub_dir: 子目录名称
            
        Returns:
            保存的文件路径
        """
        import time
        start_time = time.time()
        
        try:
            # 创建日期分层目录
            date_dir = ensure_date_structure(
                os.path.join(self.base_dir, sub_dir),
                item.fetched_at,
                self.date_format
            )
            
            # 生成文件名
            from src.tools.slugify import slugify
            filename = f"{slugify(item.title)}.md"
            file_path = os.path.join(date_dir, filename)
            
            # 写入Markdown文件
            content = self._generate_markdown(item)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 记录统计
            operation_time = time.time() - start_time
            self.stats_collector.record_file_write(
                file_path, len(content.encode('utf-8')), operation_time
            )
            
            return file_path
            
        except Exception as e:
            operation_time = time.time() - start_time
            self.stats_collector.record_file_write(
                "unknown", 0, operation_time
            )
            raise e
    
    def _generate_markdown(self, item: NewsItem) -> str:
        """生成新闻项的Markdown内容"""
        lines = []
        lines.append(f"# {item.title}")
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
            lines.append("## 摘要")
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
        "score": item.score,
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
        "score",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in items_list:
            row_out = row.copy()
            row_out["tags"] = ",".join(row_out.get("tags") or [])
            writer.writerow(row_out)

    # 排名输出（如果有分数）
    if any(r.get("score") is not None for r in items_list):
        ranked = sorted(items_list, key=lambda r: (r.get("score") or 0.0), reverse=True)
        with open(os.path.join(run_dir, "news_ranked.jsonl"), "w", encoding="utf-8") as f:
            for row in ranked:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        with open(os.path.join(run_dir, "news_ranked.csv"), "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in ranked:
                row_out = row.copy()
                row_out["tags"] = ",".join(row_out.get("tags") or [])
                writer.writerow(row_out)

    # Markdown格式导出
    markdown_dir = os.path.join(run_dir, "markdown")
    _ensure_dir(markdown_dir)
    storage = FileStorage(base_dir=markdown_dir)
    for item in items:
        try:
            storage.save_news_item(item, "news")
        except Exception:
            pass  # 忽略单个文件写入失败

    # 简单README
    readme_path = os.path.join(run_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            f"run_time: {run_time.isoformat()}\n"
            f"total_items: {len(items_list)}\n"
            f"files: news.jsonl, news.csv, news_ranked.*(if any), markdown/, analysis.json, TOP.md\n"
        )

    return run_dir
