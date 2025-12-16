from __future__ import annotations
import time
import os
from dataclasses import dataclass
import logging
from typing import List, Dict, Any, Optional
import requests
from dateutil import parser as dateparser

from config import GITHUB_CONFIG, PROJECT_PATHS, CRAWLER_CONFIG, ENCODING


@dataclass
class ReleaseItem:
    id: int
    tag_name: str
    name: str
    body: str
    html_url: str
    published_at: str

    def to_markdown(self) -> str:
        published_fmt = ''
        try:
            dt = dateparser.parse(self.published_at)
            published_fmt = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            published_fmt = self.published_at
        md = [
            f"# {self.name or self.tag_name}",
            f"- **Tag**: {self.tag_name}",
            f"- **Published At**: {published_fmt}",
            f"- **URL**: {self.html_url}",
            "\n## Notes",
            self.body or "(no content)",
            "",
        ]
        return "\n".join(md)


class GithubReleasesCrawler:
    def __init__(self, repo: str, token: Optional[str] = None) -> None:
        self.logger = logging.getLogger("sdk_release_crawler")
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'release-crawler/1.0',
        })
        # 安全处理 token：去除空白，仅在非空时设置 Authorization
        token_sanitized = (token or "").strip()
        if token_sanitized:
            # 细粒度 PAT（github_pat_ 开头）推荐使用 Bearer；经典 PAT（ghp_ 等）兼容 token
            scheme = 'Bearer' if token_sanitized.startswith('github_pat_') else 'token'
            self.session.headers['Authorization'] = f'{scheme} {token_sanitized}'
        self.base_url = GITHUB_CONFIG['base_url']
        self.per_page = int(GITHUB_CONFIG.get('per_page', 100))
        self.max_pages = int(GITHUB_CONFIG.get('max_pages', 10))
        self.delay = float(CRAWLER_CONFIG.get('request_delay', 1.0))
        self.timeout = int(CRAWLER_CONFIG.get('timeout', 30))
        self.retry_times = int(CRAWLER_CONFIG.get('retry_times', 3))

        os.makedirs(PROJECT_PATHS['releases_dir'], exist_ok=True)

    def _request(self, url: str, params: Optional[Dict[str, Any]] = None):
        last_exc: Optional[Exception] = None
        last_resp: Optional[requests.Response] = None
        removed_auth = False
        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                last_resp = resp
                if resp.status_code == 200:
                    return resp

                # 401 场景：可能是提供了无效/过期的令牌。移除 Authorization 头降级为匿名请求重试一次。
                if resp.status_code == 401 and 'Authorization' in self.session.headers and not removed_auth:
                    self.logger.warning("检测到 GitHub 401（Bad credentials?），将移除 Authorization 头并降级为未认证请求重试一次")
                    self.session.headers.pop('Authorization', None)
                    removed_auth = True
                    time.sleep(self.delay * attempt)
                    continue

                # 403 限流：根据 X-RateLimit-Reset 等头信息进行等待再重试
                if resp.status_code == 403 and ('rate limit' in (resp.text or '').lower() or resp.headers.get('X-RateLimit-Remaining') == '0'):
                    reset_at = resp.headers.get('X-RateLimit-Reset')
                    sleep_sec = self.delay * attempt
                    if reset_at:
                        try:
                            import time as _time
                            reset_ts = int(reset_at)
                            now_ts = int(_time.time())
                            # 留 1s 缓冲，最长等待 120s，避免卡死
                            sleep_sec = max(1, min(reset_ts - now_ts + 1, 120))
                        except Exception:  # noqa: BLE001
                            pass
                    if attempt < self.retry_times:
                        self.logger.warning("命中 GitHub 速率限制，等待 %.1fs 后重试（attempt=%s/%s）。建议提供有效的 GITHUB_TOKEN 以增加限额。", sleep_sec, attempt, self.retry_times)
                        time.sleep(sleep_sec)
                        continue
                    # 最后一次重试仍然限流，抛出 HTTPError
                    resp.raise_for_status()

                # 其他非 200 情况：直接抛出
                resp.raise_for_status()

            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                # 最后一次尝试直接抛出
                if attempt >= self.retry_times:
                    raise
                time.sleep(self.delay * attempt)

        # 理论上不会到这里；兜底：如果没有异常但也未返回 200，则根据最后响应抛出错误
        if last_resp is not None:
            try:
                last_resp.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                raise
        # 如果连最后响应都没有，抛出最后捕获的异常或通用错误
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("请求失败且未捕获到具体异常")

    def fetch_releases_page(self, page: int) -> List[ReleaseItem]:
        """获取指定页的 releases 列表。"""
        url = f"{self.base_url}/repos/{self.repo}/releases"
        params = {"per_page": self.per_page, "page": page}
        resp = self._request(url, params)
        data = resp.json()
        items: List[ReleaseItem] = []
        if isinstance(data, list) and data:
            for r in data:
                items.append(ReleaseItem(
                    id=r.get('id', 0),
                    tag_name=r.get('tag_name') or '',
                    name=r.get('name') or '',
                    body=r.get('body') or '',
                    html_url=r.get('html_url') or '',
                    published_at=r.get('published_at') or '',
                ))
        return items

    def fetch_releases(self, max_pages: Optional[int] = None) -> List[ReleaseItem]:
        items: List[ReleaseItem] = []
        pages = max_pages or self.max_pages
        for page in range(1, pages + 1):
            page_items = self.fetch_releases_page(page)
            if not page_items:
                break
            items.extend(page_items)
            time.sleep(self.delay)
        return items

    def save_release_markdown(self, item: ReleaseItem) -> str:
        safe_tag = item.tag_name.replace('/', '_')
        filename = f"{safe_tag or item.id}.md"
        path = os.path.join(PROJECT_PATHS['releases_dir'], filename)
        # 如果文件已存在且非空，则不重复写入
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        with open(path, 'w', encoding=ENCODING) as f:
            f.write(item.to_markdown())
        return path

    def _build_page_markdown(self, items: List[ReleaseItem], page: int) -> str:
        """构建整页的 Markdown 内容。"""
        lines: List[str] = [
            f"# Releases Page {page} - {self.repo}",
            "",
        ]
        for idx, it in enumerate(items, start=1):
            lines.append(f"## {idx}. {it.name or it.tag_name}")
            lines.append(f"- **Tag**: {it.tag_name}")
            try:
                dt = dateparser.parse(it.published_at)
                published_fmt = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                published_fmt = it.published_at
            lines.append(f"- **Published At**: {published_fmt}")
            lines.append(f"- **URL**: {it.html_url}")
            lines.append("")
            lines.append("### Notes")
            lines.append(it.body or "(no content)")
            lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def save_page_markdown(self, page: int, items: List[ReleaseItem]) -> str:
        """将某一页的所有 releases 保存为一个 Markdown 文件。文件名：仓库名+页号。"""
        repo_slug = self.repo.replace('/', '_')
        filename = f"{repo_slug}_{page}.md"
        path = os.path.join(PROJECT_PATHS['releases_dir'], filename)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        content = self._build_page_markdown(items, page)
        with open(path, 'w', encoding=ENCODING) as f:
            f.write(content)
        return path


