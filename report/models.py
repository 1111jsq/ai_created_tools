"""数据模型定义"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PaperItem:
    title: str
    authors: List[str] | str | None = None
    source: str | None = None
    published_at: Optional[str] = None
    tags: List[str] | None = None
    score: Optional[float] = None
    rank: Optional[int] = None


@dataclass
class NewsAggItem:
    title: str
    url: str
    published_at: Optional[str]
    fetched_at: str
    source: str
    source_type: str
    tags: List[str] | None = None
    score: Optional[float] = None


@dataclass
class ReleaseAggItem:
    repo: str
    tag: str
    name: str
    url: str
    published_at: str
    highlights: Optional[List[str]] = None


@dataclass
class ImageGenerationRequest:
    """图片生成请求"""
    image_type: str  # 图片类型，如 "trend_chart", "pie_chart", "architecture_diagram"
    description: str  # 图片生成的任务描述（自然语言）
    suggested_position: str  # 建议插入位置，如 "after_overview", "in_insights"
    priority: int  # 优先级（1-5，数字越大优先级越高）

