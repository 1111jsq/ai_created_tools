from __future__ import annotations

import logging
from typing import Iterable, List, Optional
from datetime import datetime, timezone
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from src.models import NewsItem
from src.sources.common import http_get, DEFAULT_HEADERS_WECHAT


log = logging.getLogger("wechat")

BASE_URL = "https://weixin.sogou.com/weixin"


def _extract_title(a_tag) -> str:
    # Sogou weixin often puts title in the tag text, sometimes in attr
    title = a_tag.get_text(strip=True)
    if title:
        return title
    for attr in ("title", "aria-label"):
        val = a_tag.get(attr)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _parse_list(html: str, query: str, name: str, tags: List[str]) -> List[NewsItem]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[NewsItem] = []
    # Typical selector: div.news-box > ul.news-list > li > div.txt-box > h3 > a
    candidates = soup.select("div.news-box ul.news-list li div.txt-box h3 a")
    if not candidates:
        # fallback: any link under news-list
        candidates = soup.select("div.news-box ul.news-list li a[href]")
    log.debug("WeChat 搜索候选: %s", len(candidates))
    for a in candidates:
        href = a.get("href") or ""
        if not href:
            continue
        title = _extract_title(a)
        url = href if href.startswith("http") else urljoin(BASE_URL, href)
        if not title or not url:
            continue
        items.append(
            NewsItem(
                source=name,
                title=title,
                url=url,
                published_at=None,
                summary=None,
                tags=tags,
                source_type="wechat",
                fetched_at=datetime.now(timezone.utc),
            )
        )
    return items


def fetch_wechat_search(name: str, query: str, tags: List[str], max_pages: int = 1) -> Iterable[NewsItem]:
    # type=2 for article search; page starts at 1
    page = 1
    total = 0
    with requests.Session() as session:
        while page <= max_pages:
            url = f"{BASE_URL}?type=2&query={quote(query)}&page={page}"
            log.debug("WeChat 搜索: page=%s url=%s", page, url)
            try:
                resp = http_get(session, url, headers=DEFAULT_HEADERS_WECHAT)
            except Exception as e:
                log.warning("WeChat 搜索失败: page=%s err=%s", page, e)
                break
            items = _parse_list(resp.text, query, name, tags)
            log.info("WeChat 完成: name=%s query=%s page=%s count=%s", name, query, page, len(items))
            for it in items:
                yield it
                total += 1
            # simple stop if page yields nothing
            if not items:
                break
            page += 1
