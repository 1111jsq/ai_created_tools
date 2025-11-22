from __future__ import annotations
import time
import os
from dataclasses import dataclass
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
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'release-crawler/1.0',
        })
        if token:
            self.session.headers['Authorization'] = f'token {token}'
        self.base_url = GITHUB_CONFIG['base_url']
        self.per_page = int(GITHUB_CONFIG.get('per_page', 100))
        self.max_pages = int(GITHUB_CONFIG.get('max_pages', 10))
        self.delay = float(CRAWLER_CONFIG.get('request_delay', 1.0))
        self.timeout = int(CRAWLER_CONFIG.get('timeout', 30))
        self.retry_times = int(CRAWLER_CONFIG.get('retry_times', 3))

        os.makedirs(PROJECT_PATHS['releases_dir'], exist_ok=True)

    def _request(self, url: str, params: Optional[Dict[str, Any]] = None):
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp
                if resp.status_code == 403 and 'rate limit' in resp.text.lower():
                    time.sleep(self.delay * attempt)
                else:
                    resp.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(self.delay * attempt)
        assert last_exc is not None
        raise last_exc

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


