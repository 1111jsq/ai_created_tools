from __future__ import annotations

import time
import logging
from typing import Dict

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger("sources.common")


class HostRateLimiter:
    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        self.min_interval = min_interval_seconds
        self._last_ts: float = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delta = now - self._last_ts
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last_ts = time.monotonic()


rate_limiter = HostRateLimiter(min_interval_seconds=1.0)


DEFAULT_HEADERS_HTML: Dict[str, str] = {
    "User-Agent": "get_agent_news/0.1 (+contact@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DEFAULT_HEADERS_RSS: Dict[str, str] = {
    "User-Agent": "get_agent_news/0.1 (+contact@example.com)",
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
}

DEFAULT_HEADERS_WECHAT: Dict[str, str] = {
    "User-Agent": "get_agent_news/0.1 (+contact@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://weixin.sogou.com/",
}


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.5, min=0.5, max=5))
def http_get(session: requests.Session, url: str, headers: Dict[str, str], timeout: float = 10.0) -> requests.Response:
    rate_limiter.wait()
    resp = session.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


