"""数据模型定义"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class BlogPost:
    """博客文章数据模型"""
    source: str                  # 博客源名称（如 "langchain"）
    title: str
    url: str
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    content: str = ""            # Markdown 格式的正文
    summary: Optional[str] = None  # 摘要（如果有）
    tags: List[str] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    url_hash: str = ""           # URL 的 SHA256 hash

    def ensure_hash(self) -> None:
        """确保 URL hash 已计算"""
        if not self.url_hash:
            self.url_hash = compute_url_hash(self.url)


def compute_url_hash(url: str) -> str:
    """计算 URL 的 SHA256 hash"""
    normalized = url.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

