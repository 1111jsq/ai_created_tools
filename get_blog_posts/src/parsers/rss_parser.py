"""RSS/Atom feed 解析器"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, List, Optional
from urllib.parse import urljoin

import feedparser
import requests
from dateutil import parser as date_parser

from src.models import BlogPost
from src.parsers.markdown_converter import html_to_markdown

logger = logging.getLogger(__name__)


DEFAULT_HEADERS_RSS = {
    "User-Agent": "get_blog_posts/0.1",
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
}


def fetch_rss_feed(
    rss_url: str,
    source: str,
    base_url: str,
    tags: List[str],
    timeout: float = 30.0,
) -> Iterable[BlogPost]:
    """从 RSS/Atom feed 抓取文章
    
    Args:
        rss_url: RSS feed URL
        source: 博客源名称
        base_url: 基础 URL（用于处理相对链接）
        tags: 标签列表
        timeout: 请求超时时间
        
    Yields:
        BlogPost 对象
    """
    logger.info("开始抓取 RSS feed: %s", rss_url)
    
    try:
        with requests.Session() as session:
            resp = session.get(rss_url, headers=DEFAULT_HEADERS_RSS, timeout=timeout)
            resp.raise_for_status()
            content = resp.content
        
        feed = feedparser.parse(content)
        status = getattr(feed, "status", None)
        bozo = getattr(feed, "bozo", None)
        logger.debug("RSS 解析: status=%s bozo=%s entries=%s", status, bozo, len(getattr(feed, "entries", [])))
        
        for entry in getattr(feed, "entries", []):
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            summary = getattr(entry, "summary", None)
            published_at = _parse_date(entry)
            
            if not title or not link:
                logger.debug("RSS 丢弃: 缺少标题或链接 title=%r link=%r", title, link)
                continue
            
            # 处理相对链接
            if not link.startswith(("http://", "https://")):
                link = urljoin(base_url, link)
            
            # 如果 RSS 中包含完整内容，使用它；否则需要后续抓取详情页
            content_html = getattr(entry, "content", None)
            if content_html:
                # 取第一个 content 项
                if isinstance(content_html, list) and content_html:
                    content_html = content_html[0].get("value", "")
                elif isinstance(content_html, dict):
                    content_html = content_html.get("value", "")
                else:
                    content_html = str(content_html) if content_html else ""
            else:
                content_html = ""
            
            # 转换为 Markdown
            content_md = html_to_markdown(content_html, base_url=link) if content_html else ""
            
            post = BlogPost(
                source=source,
                title=title,
                url=link,
                published_at=published_at,
                author=_get_author(entry),
                content=content_md,
                summary=summary,
                tags=tags,
            )
            post.ensure_hash()
            yield post
            
    except Exception as exc:
        logger.exception("RSS feed 抓取失败: %s", exc)
        raise


def _parse_date(entry: object) -> Optional[datetime]:
    """解析发布日期"""
    for field in ("published", "updated", "created"):
        value = getattr(entry, field, None)
        if value:
            try:
                dt = date_parser.parse(value)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _get_author(entry: object) -> Optional[str]:
    """提取作者信息"""
    author = getattr(entry, "author", None)
    if author:
        return str(author).strip()
    return None

