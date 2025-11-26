"""博客文章读取器"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .models import BlogAnalysisItem


def parse_iso_flexible(date_str: Optional[str]) -> Optional[datetime]:
    """灵活解析 ISO 格式日期"""
    if not date_str:
        return None
    try:
        # 尝试多种格式
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S %Z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # 如果都不匹配，尝试解析常见格式
        if "UTC" in date_str:
            date_str = date_str.replace(" UTC", "+00:00")
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z")
    except Exception:
        pass
    return None


def within_range(dt: Optional[datetime], start: datetime, end: datetime) -> bool:
    """判断日期是否在范围内"""
    if dt is None:
        return False
    return start <= dt <= end


def read_blog_post_from_markdown(md_path: Path, logger: logging.Logger) -> Optional[BlogAnalysisItem]:
    """从 Markdown 文件读取博客文章"""
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.debug("读取文件失败: %s, %s", md_path, e)
        return None
    
    # 解析 Markdown 文件
    lines = content.split("\n")
    
    # 提取标题（第一行的 # 标题）
    title = ""
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
    
    # 提取元数据
    source = ""
    url = ""
    published_at_str = None
    author = None
    tags: List[str] = []
    fetched_at_str = None
    summary = None
    body_start_idx = 0
    
    in_metadata = False
    in_summary = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 元数据部分
        if line == "## 元数据":
            in_metadata = True
            continue
        elif line.startswith("##") and in_metadata:
            in_metadata = False
        
        if in_metadata:
            if line.startswith("- **来源**: "):
                source = line.replace("- **来源**: ", "").strip()
            elif line.startswith("- **URL**: "):
                url = line.replace("- **URL**: ", "").strip()
            elif line.startswith("- **发布时间**: "):
                published_at_str = line.replace("- **发布时间**: ", "").strip()
            elif line.startswith("- **作者**: "):
                author = line.replace("- **作者**: ", "").strip()
            elif line.startswith("- **标签**: "):
                tags_str = line.replace("- **标签**: ", "").strip()
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            elif line.startswith("- **抓取时间**: "):
                fetched_at_str = line.replace("- **抓取时间**: ", "").strip()
        
        # 摘要部分
        if line == "## 摘要":
            in_summary = True
            body_start_idx = i + 1
            continue
        elif line == "## 正文" or (line.startswith("##") and in_summary):
            if in_summary and not line.startswith("## 正文"):
                # 摘要结束
                summary_lines = lines[body_start_idx:i]
                summary = "\n".join(summary_lines).strip()
            in_summary = False
            if line == "## 正文":
                body_start_idx = i + 1
                break
        elif in_summary:
            continue
    
    # 提取正文
    body_lines = lines[body_start_idx:] if body_start_idx < len(lines) else []
    body_content = "\n".join(body_lines).strip()
    
    # 如果标题为空，尝试从文件名推断
    if not title and md_path.stem:
        title = md_path.stem.replace("-", " ").title()
    
    # 如果来源为空，尝试从路径推断
    if not source:
        # 路径格式: .../markdown/markdown/<source>/YYYY/MM/DD/file.md
        parts = md_path.parts
        for i, part in enumerate(parts):
            if part == "markdown" and i + 1 < len(parts):
                if parts[i + 1] == "markdown" and i + 2 < len(parts):
                    source = parts[i + 2]
                    break
    
    return BlogAnalysisItem(
        source=source or "unknown",
        title=title or md_path.stem,
        url=url or "",
        published_at=published_at_str,
        author=author,
        summary=summary,
        tags=tags,
        content=body_content,
        fetched_at=fetched_at_str,
    )


def read_blog_posts(
    exports_root: Path,
    start_dt: Optional[datetime] = None,
    end_dt: Optional[datetime] = None,
    source_filter: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> List[BlogAnalysisItem]:
    """读取博客文章"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    items: List[BlogAnalysisItem] = []
    
    if not exports_root.exists():
        logger.info("博客导出根目录不存在: %s", str(exports_root))
        return items
    
    # 遍历所有导出目录
    for run_dir in sorted(exports_root.iterdir()):
        if not run_dir.is_dir():
            continue
        
        # 查找 markdown 目录
        markdown_root = run_dir / "markdown" / "markdown"
        if not markdown_root.exists():
            # 也可能在 markdown 目录下直接有源目录
            markdown_root = run_dir / "markdown"
            if not markdown_root.exists():
                continue
        
        # 遍历所有源目录
        for source_dir in markdown_root.iterdir():
            if not source_dir.is_dir():
                continue
            
            source_name = source_dir.name
            if source_filter and source_name != source_filter:
                continue
            
            # 递归遍历日期目录结构 YYYY/MM/DD/file.md
            for md_file in source_dir.rglob("*.md"):
                if not md_file.is_file():
                    continue
                
                item = read_blog_post_from_markdown(md_file, logger)
                if not item:
                    continue
                
                # 时间过滤
                if start_dt and end_dt:
                    pub_dt = parse_iso_flexible(item.published_at)
                    fetched_dt = parse_iso_flexible(item.fetched_at)
                    basis_dt = pub_dt or fetched_dt
                    
                    if not basis_dt:
                        # 如果没有日期信息，尝试从文件名或路径推断
                        # 路径格式: .../YYYY/MM/DD/file.md
                        parts = md_file.parts
                        try:
                            year_idx = -1
                            for i, part in enumerate(parts):
                                if part.isdigit() and len(part) == 4:
                                    year_idx = i
                                    break
                            if year_idx >= 0 and year_idx + 2 < len(parts):
                                year = int(parts[year_idx])
                                month = int(parts[year_idx + 1])
                                day = int(parts[year_idx + 2])
                                basis_dt = datetime(year, month, day, tzinfo=timezone.utc)
                        except (ValueError, IndexError):
                            pass
                    
                    if basis_dt and not within_range(basis_dt, start_dt, end_dt):
                        continue
                
                items.append(item)
    
    logger.info("读取到 %d 篇博客文章", len(items))
    return items

