"""文件存储管理"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.models import BlogPost


def slugify(title: Optional[str]) -> str:
    """生成 URL 友好的 slug"""
    import re
    if not title:
        return "untitled"
    title = title.strip().lower()
    title = re.sub(r"\s+", "-", title)
    title = re.sub(r"[^a-z0-9\-]+", "-", title)
    title = re.sub(r"-{2,}", "-", title)
    return title.strip("-") or "untitled"


def ensure_date_structure(base_dir: str, date: Optional[datetime] = None, date_format: str = "%Y/%m/%d") -> str:
    """确保日期分层目录结构存在"""
    if date is None:
        date = datetime.now()
    date_path = date.strftime(date_format)
    full_path = os.path.join(base_dir, date_path)
    os.makedirs(full_path, exist_ok=True)
    return full_path


class FileStorage:
    """文件系统存储管理器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def save_blog_post(self, post: BlogPost, sub_dir: str = "markdown", overwrite: bool = False) -> Optional[str]:
        """保存单个博客文章到文件系统
        
        Args:
            post: 博客文章对象
            sub_dir: 子目录名称
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            保存的文件路径，如果已存在且不覆盖则返回 None
        """
        # 确定日期（优先使用 published_at，否则使用 fetched_at）
        date = post.published_at or post.fetched_at
        
        # 创建日期分层目录: <base_dir>/<sub_dir>/<source>/<YYYY>/<MM>/<DD>/
        source_dir = os.path.join(self.base_dir, sub_dir, post.source)
        date_dir = ensure_date_structure(source_dir, date)
        
        # 生成文件名（使用 slug）
        slug = slugify(post.title)
        filename = f"{slug}.md"
        file_path = os.path.join(date_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0 and not overwrite:
            return None
        
        # 生成 Markdown 内容
        content = self._generate_markdown(post)
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return file_path
    
    def _generate_markdown(self, post: BlogPost) -> str:
        """生成博客文章的 Markdown 内容"""
        lines = []
        
        # 标题
        lines.append(f"# {post.title}")
        lines.append("")
        
        # 元数据
        lines.append("## 元数据")
        lines.append("")
        lines.append(f"- **来源**: {post.source}")
        lines.append(f"- **URL**: {post.url}")
        if post.published_at:
            lines.append(f"- **发布时间**: {post.published_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if post.author:
            lines.append(f"- **作者**: {post.author}")
        if post.tags:
            lines.append(f"- **标签**: {', '.join(post.tags)}")
        lines.append(f"- **抓取时间**: {post.fetched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        
        # 摘要（如果有）
        if post.summary:
            lines.append("## 摘要")
            lines.append("")
            lines.append(post.summary)
            lines.append("")
        
        # 正文
        lines.append("## 正文")
        lines.append("")
        lines.append(post.content)
        
        return "\n".join(lines)
    
    def save_blog_posts(
        self,
        posts: List[BlogPost],
        sub_dir: str = "markdown",
        overwrite: bool = False,
    ) -> List[str]:
        """批量保存博客文章
        
        Args:
            posts: 博客文章列表
            sub_dir: 子目录名称
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            保存的文件路径列表
        """
        saved_paths = []
        for post in posts:
            path = self.save_blog_post(post, sub_dir=sub_dir, overwrite=overwrite)
            if path:
                saved_paths.append(path)
        return saved_paths


def save_posts_to_directory(
    posts: List[BlogPost],
    base_dir: str,
    run_time: Optional[datetime] = None,
    overwrite: bool = False,
) -> str:
    """保存文章到导出目录
    
    Args:
        posts: 文章列表
        base_dir: 基础目录
        run_time: 运行时间（用于创建时间戳目录）
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        导出目录路径
    """
    run_time = run_time or datetime.now()
    run_dir_name = run_time.strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, run_dir_name)
    os.makedirs(run_dir, exist_ok=True)
    
    # 保存 Markdown 文件
    markdown_dir = os.path.join(run_dir, "markdown")
    storage = FileStorage(base_dir=markdown_dir)
    saved_paths = storage.save_blog_posts(posts, overwrite=overwrite)
    
    # 生成 README
    readme_path = os.path.join(run_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            f"run_time: {run_time.isoformat()}\n"
            f"total_posts: {len(posts)}\n"
            f"saved_posts: {len(saved_paths)}\n"
            f"files: markdown/\n"
        )
    
    return run_dir

