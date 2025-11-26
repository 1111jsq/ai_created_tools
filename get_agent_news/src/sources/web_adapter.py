from __future__ import annotations

import logging
from typing import Iterable, List, Optional, Dict, Any, Set
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup

from src.models import NewsItem
from src.sources.common import http_get, DEFAULT_HEADERS_HTML
from src.tools.nested import get_from_path, render_value


log = logging.getLogger("web")

def _extract_title(el, title_attr: str) -> str:
    if title_attr == "text":
        title = el.get_text(strip=True)
        if title:
            return title
    else:
        val = el.get(title_attr)
        if isinstance(val, str) and val.strip():
            return val.strip()
    for attr in ("title", "aria-label", "alt"):
        val = el.get(attr)
        if isinstance(val, str) and val.strip():
            return val.strip()
    # try first child text
    if el.contents:
        txt = " ".join([getattr(c, "strip", lambda: "")() if isinstance(c, str) else c.get_text(strip=True) for c in el.contents])
        if txt.strip():
            return txt.strip()
    return ""


def _get_from_path(obj: Any, path: str) -> Any:
    """从嵌套字典/列表中按点路径提取字段，例如 data.items.0.title"""
    return get_from_path(obj, path)


def _render_value(val: Any, variables: Dict[str, Any]) -> Any:
    return render_value(val, variables)


def _get_first_by_paths(obj: Any, paths: Any) -> Any:
    """在给定的多个路径中依次查找第一个非空值。paths 可以是字符串或字符串列表。"""
    if obj is None or paths is None:
        return None
    if isinstance(paths, str):
        return _get_from_path(obj, paths)
    if isinstance(paths, list):
        for p in paths:
            v = _get_from_path(obj, p)
            if v not in (None, ""):
                return v
    return None


def fetch_web(
    name: str,
    url: str,
    selector_item: str,
    url_attr: str = "href",
    title_attr: str = "text",
    include_keywords: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    pagination: Optional[Dict[str, Any]] = None,
) -> Iterable[NewsItem]:
    """按配置抓取 Web 列表页面，支持翻页。

    pagination 配置（可选）：
      - type: "param" | "next"（默认无翻页）
      - max_pages: 最大页数，默认 1
      - 当 type=param:
          - param_name: 查询参数名，如 "page"
          - start: 起始页码（含），默认 1
          - step: 步长，默认 1
          - stop_on_empty: 若某页无任何命中则提前停止（默认 true）
      - 当 type=next:
          - next_selector: 下一页链接的 CSS 选择器
          - next_url_attr: 链接属性名，默认 "href"
          - stop_on_empty: 若某页无任何命中则提前停止（默认 true）
    """

    tags = tags or []
    include_keywords = include_keywords or []
    pagination = pagination or {}

    max_pages = int(pagination.get("max_pages", 1) or 1)
    p_type = (pagination.get("type") or "").lower()
    stop_on_empty = bool(pagination.get("stop_on_empty", True))

    log.info(
        "Web 抓取开始: name=%s url=%s selector=%s pagination=%s",
        name, url, selector_item, pagination or {}
    )

    def build_url_with_param(base_url: str, param_name: str, param_value: int) -> str:
        parsed = urlparse(base_url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        qs[param_name] = [str(param_value)]
        new_query = urlencode(qs, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    produced = 0
    seen_links: Set[str] = set()

    with requests.Session() as session:
        current_url = url

        # JSON API 模式：适配滚动/接口分页，忽略 HTML 选择器
        if p_type == "json_api":
            api_url = pagination.get("api_url")
            method = (pagination.get("method") or "GET").upper()
            list_path = pagination.get("list_path") or pagination.get("list_paths")
            url_path = pagination.get("url_path") or pagination.get("url_paths")
            title_path = pagination.get("title_path") or pagination.get("title_paths")
            published_path = pagination.get("published_path")
            summary_path = pagination.get("summary_path")
            url_template = pagination.get("url_template")
            headers_override = pagination.get("headers") or {}
            params_tmpl = pagination.get("params") or {}
            json_tmpl = pagination.get("json") or {}
            base_for_join = pagination.get("base_url") or url
            next_vars = pagination.get("next_vars") or {}

            # 允许使用 url_path 或 url_template 其一，用于构造详情链接
            if (not api_url) or (not list_path) or (not title_path) or ((not url_path) and (not url_template)):
                log.info(
                    "Web JSON API 配置不完整，跳过: name=%s api_url=%s list_path=%s title_path=%s url_path/url_template=%s/%s",
                    name, bool(api_url), bool(list_path), bool(title_path), bool(url_path), bool(url_template)
                )
                return

            produced_api = 0
            try:
                prev_vars: Dict[str, Any] = {"page_callback": ""}
                for page_idx in range(1, max_pages + 1):
                    variables = {
                        "page": page_idx,
                        "ts": 0,
                        "page_event": 1 if page_idx == 1 else 2,
                        "page_callback": prev_vars.get("page_callback", ""),
                    }
                    req_url = _render_value(api_url, variables)
                    req_params = _render_value(params_tmpl, variables)
                    req_json = _render_value(json_tmpl, variables)

                    if method == "POST":
                        resp = session.post(
                            req_url,
                            headers={**DEFAULT_HEADERS_HTML, **headers_override},
                            params=req_params or None,
                            json=req_json or None,
                            timeout=10.0,
                        )
                    else:
                        # 对 GET 使用共有 http_get（不含 params），若存在 params 则回退到 session.get
                        if req_params:
                            resp = session.get(req_url, headers={**DEFAULT_HEADERS_HTML, **headers_override}, params=req_params or None, timeout=10.0)
                        else:
                            resp = http_get(session, req_url, headers={**DEFAULT_HEADERS_HTML, **headers_override})
                    resp.raise_for_status()
                    try:
                        data = resp.json()
                    except Exception as exc:
                        log.warning("Web JSON API 解码失败: name=%s page=%s url=%s err=%s", name, page_idx, req_url, exc)
                        if stop_on_empty:
                            break
                        else:
                            continue
                    items = _get_first_by_paths(data, list_path) or []
                    log.info(
                        "Web JSON API: name=%s page=%s url=%s items=%s",
                        name, page_idx, req_url, len(items) if isinstance(items, list) else type(items)
                    )

                    page_produced = 0
                    if isinstance(items, list):
                        for it in items:
                            title = _get_first_by_paths(it, title_path)
                            # 先优先使用 url_path 抽取，若无则用 url_template 渲染
                            link = _get_first_by_paths(it, url_path) if url_path else None
                            if (not link) and url_template:
                                try:
                                    # 允许使用顶层字段进行模板渲染
                                    link = _render_value(url_template, {**variables, **(it if isinstance(it, dict) else {})})
                                except Exception:
                                    link = None
                            if not isinstance(title, str) or not isinstance(link, str):
                                continue
                            link_full = urljoin(base_for_join, link)
                            summary_val = _get_from_path(it, summary_path) if summary_path else None
                            # 解析发布时间（可选）
                            published_at_val = None
                            if published_path:
                                try:
                                    raw_dt = _get_from_path(it, published_path)
                                    if isinstance(raw_dt, str) and raw_dt.strip():
                                        s = raw_dt.strip().replace("/", "-")
                                        # 常见格式：YYYY-MM-DD HH:MM:SS
                                        try:
                                            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
                                        except Exception:
                                            # 若只含日期
                                            try:
                                                dt = datetime.strptime(s, "%Y-%m-%d")
                                            except Exception:
                                                dt = None
                                        if dt is not None:
                                            published_at_val = dt.replace(tzinfo=timezone.utc)
                                except Exception:
                                    published_at_val = None
                            summary_text = str(summary_val) if isinstance(summary_val, (str, int, float)) else None

                            if include_keywords:
                                lowered = title.lower()
                                if not any(k.lower() in lowered for k in include_keywords):
                                    continue

                            if link_full in seen_links:
                                continue
                            seen_links.add(link_full)

                            produced += 1
                            produced_api += 1
                            page_produced += 1
                            yield NewsItem(
                                source=name,
                                title=str(title),
                                url=link_full,
                                published_at=published_at_val,
                                summary=summary_text,
                                tags=tags,
                                source_type="web",
                                fetched_at=datetime.now(timezone.utc),
                            )

                    if page_produced == 0 and stop_on_empty:
                        log.info("Web JSON API 提前停止: name=%s page=%s 无命中", name, page_idx)
                        break

                    # 更新翻页变量供下一页使用
                    if isinstance(next_vars, dict) and next_vars:
                        for var_name, path in next_vars.items():
                            if isinstance(path, list):
                                val = _get_first_by_paths(data, path)
                            else:
                                val = _get_from_path(data, path)
                            if val is not None:
                                prev_vars[var_name] = val
                                try:
                                    _preview = str(val)
                                    if len(_preview) > 60:
                                        _preview = _preview[:60] + "..."
                                except Exception:
                                    _preview = "<non-str>"
                                log.info("Web JSON API 翻页变量: name=%s %s=%s", name, var_name, _preview)
            except Exception as exc:
                log.exception("Web JSON API 失败: name=%s err=%s", name, exc)

            log.info("Web JSON API 产生条目: name=%s total=%s", name, produced_api)
            # 若 JSON API 成功产出条目，则返回；否则继续走 HTML 保底
            if produced_api > 0:
                return

        # PAGE_LINKS 模式：从第一页提取页码链接，抓取后续页面
        if p_type == "page_links":
            links_selector = pagination.get("links_selector", ".pagination a, .pager a, .page-numbers a")

            # 先抓取第一页
            resp = http_get(session, current_url, headers=DEFAULT_HEADERS_HTML)
            log.info("Web 页面获取: name=%s page=%s status=%s url=%s", name, 1, resp.status_code, current_url)
            soup = BeautifulSoup(resp.text, "html.parser")

            elements = soup.select(selector_item)
            log.info("Web 选择器命中: name=%s page=%s count=%s", name, 1, len(elements))

            page_produced = 0
            for el in elements:
                title = _extract_title(el, title_attr)
                if url_attr == "href":
                    link = urljoin(current_url, el.get("href") or "")
                else:
                    link = urljoin(current_url, el.get(url_attr) or "")
                if not title or not link:
                    continue
                if include_keywords:
                    lowered = title.lower()
                    if not any(k.lower() in lowered for k in include_keywords):
                        continue
                if link in seen_links:
                    continue
                seen_links.add(link)
                produced += 1
                page_produced += 1
                yield NewsItem(
                    source=name,
                    title=title,
                    url=link,
                    published_at=None,
                    summary=None,
                    tags=tags,
                    source_type="web",
                    fetched_at=datetime.now(timezone.utc),
                )

            # 提取分页链接
            page_links = []
            for a in soup.select(links_selector):
                href = a.get("href")
                if not href:
                    continue
                link_full = urljoin(current_url, href)
                if link_full not in page_links and link_full != current_url:
                    page_links.append(link_full)

            # 如果未发现分页链接，尝试基于 URL 的回退规则合成分页 URL（?page=N 与 /page/N）
            if not page_links:
                fallback_links = []
                try:
                    from urllib.parse import urlparse, urlunparse
                    parsed = urlparse(current_url)
                    base_path = parsed.path.rstrip("/")
                    for n in range(2, max_pages + 1):
                        # 尝试 query 参数方式
                        fallback_links.append(build_url_with_param(current_url, "page", n))
                        # 尝试路径方式 /page/N
                        new_path = f"{base_path}/page/{n}"
                        fallback_links.append(urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment)))
                except Exception:
                    fallback_links = []
                # 去重并剔除当前页
                uniq_fb = []
                for u in fallback_links:
                    if u and u != current_url and u not in uniq_fb:
                        uniq_fb.append(u)
                page_links = uniq_fb
                log.info("Web 分页链接为空，使用回退 URL: name=%s candidates=%s", name, min(len(page_links), max_pages - 1))

            # 选取最多 max_pages-1 个后续页面
            follow_links = page_links[: max_pages - 1]
            log.info("Web 分页链接: name=%s found=%s used=%s selector=%s", name, len(page_links), len(follow_links), links_selector)

            page_num = 2
            for link_url in follow_links:
                resp2 = http_get(session, link_url, headers=DEFAULT_HEADERS_HTML)
                log.info("Web 页面获取: name=%s page=%s status=%s url=%s", name, page_num, resp2.status_code, link_url)
                soup2 = BeautifulSoup(resp2.text, "html.parser")
                elements2 = soup2.select(selector_item)
                log.info("Web 选择器命中: name=%s page=%s count=%s", name, page_num, len(elements2))
                page_produced2 = 0
                for el in elements2:
                    title = _extract_title(el, title_attr)
                    if url_attr == "href":
                        link = urljoin(link_url, el.get("href") or "")
                    else:
                        link = urljoin(link_url, el.get(url_attr) or "")
                    if not title or not link:
                        continue
                    if include_keywords:
                        lowered = title.lower()
                        if not any(k.lower() in lowered for k in include_keywords):
                            continue
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    produced += 1
                    page_produced2 += 1
                    yield NewsItem(
                        source=name,
                        title=title,
                        url=link,
                        published_at=None,
                        summary=None,
                        tags=tags,
                        source_type="web",
                        fetched_at=datetime.now(timezone.utc),
                    )
                if page_produced2 == 0 and stop_on_empty:
                    log.info("Web 提前停止: name=%s page=%s 无命中", name, page_num)
                    break
                page_num += 1
            log.info("Web 产生条目: name=%s total=%s", name, produced)
            return

        # HTML 翻页
        for page_idx in range(1, max_pages + 1):
            # 计算本页 URL
            if p_type == "param":
                param_name = pagination.get("param_name", "page")
                start = int(pagination.get("start", 1) or 1)
                step = int(pagination.get("step", 1) or 1)
                page_value = start + (page_idx - 1) * step
                page_url = build_url_with_param(url, param_name, page_value)
            else:
                page_url = current_url

            resp = http_get(session, page_url, headers=DEFAULT_HEADERS_HTML)
            log.info("Web 页面获取: name=%s page=%s status=%s url=%s", name, page_idx, resp.status_code, page_url)
            soup = BeautifulSoup(resp.text, "html.parser")

            elements = soup.select(selector_item)
            log.info("Web 选择器命中: name=%s page=%s count=%s", name, page_idx, len(elements))

            page_produced = 0
            for el in elements:
                title = _extract_title(el, title_attr)
                if url_attr == "href":
                    link = urljoin(page_url, el.get("href") or "")
                else:
                    link = urljoin(page_url, el.get(url_attr) or "")

                if not title or not link:
                    log.debug("Web 丢弃: 缺少标题或链接 title=%r link=%r", title, link)
                    continue

                if include_keywords:
                    lowered = title.lower()
                    if not any(k.lower() in lowered for k in include_keywords):
                        continue

                if link in seen_links:
                    continue
                seen_links.add(link)

                produced += 1
                page_produced += 1
                yield NewsItem(
                    source=name,
                    title=title,
                    url=link,
                    published_at=None,
                    summary=None,
                    tags=tags,
                    source_type="web",
                    fetched_at=datetime.now(timezone.utc),
                )

            if page_produced == 0 and stop_on_empty:
                log.info("Web 提前停止: name=%s page=%s 无命中", name, page_idx)
                break

            # 计算下一页 URL（当 type=next）
            if p_type == "next":
                next_selector = pagination.get("next_selector")
                next_attr = pagination.get("next_url_attr", "href")
                if not next_selector:
                    log.info("Web 翻页配置缺少 next_selector，停止 name=%s page=%s", name, page_idx)
                    break
                next_el = soup.select_one(next_selector)
                if not next_el:
                    log.info("Web 未找到下一页链接，停止 name=%s page=%s", name, page_idx)
                    break
                next_href = next_el.get(next_attr)
                if not next_href:
                    log.info("Web 下一页元素缺少链接属性 %s，停止 name=%s page=%s", next_attr, name, page_idx)
                    break
                current_url = urljoin(page_url, next_href)
                log.info("Web 下一页地址: name=%s next_url=%s", name, current_url)

    log.info("Web 产生条目: name=%s total=%s", name, produced)
