"""博客分析数据模型"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class BlogAnalysisItem:
    """博客分析项"""
    source: str                    # 来源（如 "langchain", "anthropic"）
    title: str
    url: str
    published_at: Optional[str]    # ISO 格式日期字符串
    author: Optional[str]
    summary: Optional[str]          # 摘要
    tags: List[str]
    content: str                   # 正文内容（可能很长）
    fetched_at: Optional[str]      # 抓取时间

