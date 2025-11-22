from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import hashlib


@dataclass
class NewsItem:
    source: str
    title: str
    url: str
    published_at: Optional[datetime]
    summary: Optional[str]
    tags: List[str] = field(default_factory=list)
    source_type: str = "rss"  # rss | web
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    url_hash: str = ""
    score: Optional[float] = None  # ranking score 0..1

    def ensure_hash(self) -> None:
        if not self.url_hash:
            self.url_hash = compute_url_hash(self.url)


def compute_url_hash(url: str) -> str:
    normalized = url.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
