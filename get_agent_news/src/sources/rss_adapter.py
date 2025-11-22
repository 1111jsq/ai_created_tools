from __future__ import annotations

import logging
from typing import Iterable, List
from datetime import datetime, timezone
from dateutil import parser as date_parser

import requests
import feedparser

from src.models import NewsItem
from src.sources.common import http_get, DEFAULT_HEADERS_RSS


log = logging.getLogger("rss")


def fetch_rss(name: str, url: str, tags: List[str]) -> Iterable[NewsItem]:
    log.debug("RSS 抓取开始: name=%s url=%s", name, url)
    with requests.Session() as session:
        resp = http_get(session, url, headers=DEFAULT_HEADERS_RSS)
        log.debug("RSS 响应: status=%s len=%s", resp.status_code, len(resp.content))
        content = resp.content
    feed = feedparser.parse(content)
    status = getattr(feed, "status", None)
    bozo = getattr(feed, "bozo", None)
    log.debug("RSS 解析: status=%s bozo=%s entries=%s", status, bozo, len(getattr(feed, "entries", [])))
    for entry in getattr(feed, "entries", []):
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        summary = getattr(entry, "summary", None)
        published_at = _parse_date(entry)
        if not title or not link:
            log.debug("RSS 丢弃: 缺少标题或链接 title=%r link=%r", title, link)
            continue
        yield NewsItem(
            source=name,
            title=title,
            url=link,
            published_at=published_at,
            summary=summary,
            tags=tags,
            source_type="rss",
        )


def _parse_date(entry: object) -> datetime | None:
    # Try various known fields
    for field in ("published", "updated", "created"):
        value = getattr(entry, field, None)
        if value:
            try:
                dt = date_parser.parse(value)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None
