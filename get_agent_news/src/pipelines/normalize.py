from __future__ import annotations

from typing import Iterable, List
from datetime import datetime, timezone

from src.models import NewsItem


def normalize_items(items: Iterable[NewsItem]) -> List[NewsItem]:
    normalized: List[NewsItem] = []
    for item in items:
        item.title = item.title.strip()
        item.url = item.url.strip()
        item.summary = (item.summary or "").strip() or None
        if item.published_at and item.published_at.tzinfo is None:
            item.published_at = item.published_at.replace(tzinfo=timezone.utc)
        item.ensure_hash()
        normalized.append(item)
    return normalized
