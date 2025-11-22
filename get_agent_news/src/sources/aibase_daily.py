from __future__ import annotations

import os
import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup


log = logging.getLogger("aibase_daily")

from src.sources.common import http_get, DEFAULT_HEADERS_HTML, rate_limiter
from src.tools.nested import get_from_path, render_value


def _fetch_robots_disallows(session: requests.Session, site_root: str) -> list[str]:
	"""
	最小解析 robots.txt，提取针对 User-agent: * 的 Disallow 规则。
	"""
	try:
		rtxt = http_get(session, site_root.rstrip("/") + "/robots.txt", headers=DEFAULT_HEADERS_HTML, timeout=5.0).text
	except Exception:
		return []
	lines = [ln.strip() for ln in rtxt.splitlines()]
	disallows: list[str] = []
	active = False
	for ln in lines:
		if not ln or ln.startswith("#"):
			continue
		k, sep, v = ln.partition(":")
		if sep != ":":
			continue
		key = k.strip().lower()
		val = v.strip()
		if key == "user-agent":
			active = (val == "*" or val == '"*"')
			continue
		if not active:
			continue
		if key == "disallow":
			disallows.append(val or "/")
	return disallows


def _path_disallowed(path: str, disallows: list[str]) -> bool:
	for rule in disallows:
		if not rule:
			continue
		# 完全禁止
		if rule == "/":
			return True
		if path.startswith(rule):
			return True
	return False


def _build_url_with_param(base_url: str, param_name: str, param_value: int) -> str:
    parsed = urlparse(base_url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs[param_name] = [str(param_value)]
    new_query = urlencode(qs, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def _detect_date(text: str) -> Optional[str]:
    """从文本中解析出日期，支持多种格式：
    - 2025-11-03 / 2025/11/03
    - 2025年11月3日 / 2025年11月3号 15:59
    - 11-03 或 11/03（缺少年份时使用当前年份）
    """
    if not text:
        return None
    # 1) 优先匹配中文格式：YYYY年M月D日/号 可带时间
    m = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]?", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except Exception:
            pass
    # 2) 标准格式 YYYY-MM-DD / YYYY/MM/DD
    m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except Exception:
            pass
    # 3) 仅月日：MM-DD / MM/DD（缺少年份，取当前年）
    m = re.search(r"(\d{1,2})[-/](\d{1,2})", text)
    if m:
        now = datetime.now()
        mo, d = int(m.group(1)), int(m.group(2))
        try:
            return datetime(now.year, mo, d).strftime("%Y-%m-%d")
        except Exception:
            pass
    return None


def _extract_daily_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    links: List[str] = []
    # 常见：/zh/daily/12345 或含 daily 的详情页
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        if "/zh/daily/" in href:
            full = urljoin(base_url, href)
            if full not in links:
                links.append(full)
    return links


def _extract_article_markdown(soup: BeautifulSoup, page_url: str) -> str:
    # 标题
    title_el = soup.select_one("h1, .post-title, .article-title, header h1")
    title = (title_el.get_text(strip=True) if title_el else "AIbase 日报")

    # 日期（优先从“发布时间”附近提取；再尝试 meta；最后全文兜底）
    date_str: Optional[str] = None
    # 1) 查找包含“发布时间”的元素
    candidates_text = []
    for el in soup.find_all(string=re.compile("发布时间|发布于|发布日期")):
        try:
            ctx = el.parent.get_text(" ", strip=True)
            if ctx:
                candidates_text.append(ctx)
        except Exception:
            continue
    for ctx in candidates_text:
        date_str = _detect_date(ctx)
        if date_str:
            break
    # 2) meta/time 或常见日期类
    if not date_str:
        date_meta = soup.select_one("meta[property='article:published_time'], time[datetime], time, .post-date, .article-date, .date, .publish-time")
        if date_meta:
            date_text = date_meta.get("content") or date_meta.get("datetime") or date_meta.get_text(strip=True)
            date_str = _detect_date(date_text or "")
    # 3) 全文兜底
    if not date_str:
        date_str = _detect_date(soup.get_text(" ", strip=True))
    # 4) 仍未解析则使用今天（避免为空）
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 正文容器
    container = None
    candidates = [
        "article",
        ".article",
        ".post",
        ".content",
        ".post-content",
        "main",
        "#content",
    ]
    for sel in candidates:
        container = soup.select_one(sel)
        if container:
            break
    container = container or soup

    lines: List[str] = []
    for h in container.select("h2, h3, h4"):
        text = h.get_text(" ", strip=True)
        if text:
            lines.append(f"- {text}")
    for li in container.select("li"):
        text = li.get_text(" ", strip=True)
        if text:
            lines.append(f"- {text}")
    # 补充段落（去重）
    seen = set(lines)
    for p in container.select("p"):
        text = p.get_text(" ", strip=True)
        if text and text not in seen:
            lines.append(text)
            seen.add(text)

    log.info("AIbase 日报日期解析: url=%s date=%s", page_url, date_str)
    md = [f"# {title}", "", f"来源：{page_url}", f"日期：{date_str}", ""]
    md.extend(lines)
    md.append("")
    return "\n".join(md)


def _get_from_path(obj: Any, path: str) -> Any:
    return get_from_path(obj, path)


def _render_value(val: Any, variables: Dict[str, Any]) -> Any:
    return render_value(val, variables)


def export_aibase_daily(
    daily_url: str,
    output_dir: str = os.path.join("content"),
    max_pages: int = 3,
    api_config: Optional[Dict[str, Any]] = None,
    stop_on_duplicate: bool = True,
    storage: Optional[Any] = None,
    respect_robots: bool = True,
    host_rate_limit_s: Optional[float] = None,
) -> List[str]:
    """抓取 AIbase 日报，优先通过 JSON API 获取列表，再逐条详情页转为 Markdown 文件。
    返回写入的文件路径列表。
    """
    os.makedirs(output_dir, exist_ok=True)
    written: List[str] = []
    written_dates: set[str] = set()

    def _url_hash(url: str) -> str:
        import hashlib
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    # 可配置的主机级速率
    if isinstance(host_rate_limit_s, (int, float)) and host_rate_limit_s and host_rate_limit_s > 0:
        rate_limiter.min_interval = float(host_rate_limit_s)

    with requests.Session() as session:
        # robots 检查（页面抓取前）
        if respect_robots:
            parsed = urlparse(daily_url)
            site_root = f"{parsed.scheme}://{parsed.netloc}"
            disallows = _fetch_robots_disallows(session, site_root)
            if _path_disallowed(parsed.path or "/", disallows):
                log.warning("robots.txt 禁止抓取该路径，已跳过: host=%s path=%s", parsed.netloc, parsed.path or "/")
                return written

        if api_config:
            api_url = api_config.get("url")
            method = (api_config.get("method") or "GET").upper()
            headers_override = api_config.get("headers") or {}
            params_tmpl = api_config.get("params") or {}
            list_path = api_config.get("list_path")
            title_path = api_config.get("title_path")
            date_path = api_config.get("date_path")
            oid_path = api_config.get("oid_path")
            detail_template = api_config.get("url_template")

            if not api_url or not list_path or not title_path or not (oid_path or detail_template):
                log.warning("AIbase 日报 API 配置不完整，回退到 HTML：%s", api_config)
            else:
                stop_flag = False
                for page_idx in range(1, max_pages + 1):
                    variables = {"page": page_idx, "ts": int(time.time() * 1000)}
                    req_url = _render_value(api_url, variables)
                    req_params = _render_value(params_tmpl, variables)
                    if method == "POST":
                        resp = session.post(req_url, headers={**DEFAULT_HEADERS_HTML, **headers_override}, json=req_params, timeout=10.0)
                    else:
                        if params_tmpl:
                            resp = session.get(req_url, headers={**DEFAULT_HEADERS_HTML, **headers_override}, params=req_params, timeout=10.0)
                        else:
                            resp = http_get(session, req_url, headers={**DEFAULT_HEADERS_HTML, **headers_override}, timeout=10.0)
                    resp.raise_for_status()
                    data = resp.json()
                    items = _get_from_path(data, list_path) or []
                    log.info("AIbase 日报 API: page=%s url=%s items=%s", page_idx, req_url, len(items) if isinstance(items, list) else type(items))
                    if not isinstance(items, list) or not items:
                        if page_idx > 1:
                            log.info("AIbase 日报空页停止: page=%s url=%s", page_idx, req_url)
                            break
                        log.info("AIbase 日报当前页为空，尝试下一页: page=%s url=%s", page_idx, req_url)
                        continue
                    for it in items:
                        title = _get_from_path(it, title_path)
                        date_text = _get_from_path(it, date_path) if date_path else None
                        date_str = _detect_date(str(date_text) if date_text else "") or datetime.now().strftime("%Y-%m-%d")
                        oid = _get_from_path(it, oid_path) if oid_path else None
                        detail_url = None
                        if detail_template and (oid is not None):
                            try:
                                detail_url = _render_value(detail_template, {"oid": oid})
                            except Exception:
                                detail_url = None
                        if not detail_url and oid:
                            detail_url = urljoin(daily_url, str(oid))
                        if not detail_url:
                            log.warning("AIbase 日报缺少详情链接，跳过: title=%s", title)
                            continue

                        # 重复检测（文件与本轮日期）
                        u_hash = _url_hash(detail_url)
                        # 文件存在性（以日期文件为准）也视为重复
                        base_name_probe = f"{date_str}.md"
                        legacy_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "data", "daily"))
                        if stop_on_duplicate and (os.path.exists(os.path.join(output_dir, base_name_probe)) or os.path.exists(os.path.join(legacy_dir, base_name_probe))):
                            log.info("AIbase 日报命中已存在日期文件，停止继续分页: date=%s page=%s", date_str, page_idx)
                            stop_flag = True
                            break
                        # 本轮运行内若同日期已写过，也直接停止，不生成 _2 文件
                        if stop_on_duplicate and date_str in written_dates:
                            log.info("AIbase 日报本轮已写入同日期，停止继续分页: date=%s page=%s", date_str, page_idx)
                            stop_flag = True
                            break

                        try:
                            dr = http_get(session, detail_url, headers=DEFAULT_HEADERS_HTML)
                            dsoup = BeautifulSoup(dr.text, "html.parser")
                            md = _extract_article_markdown(dsoup, detail_url)
                            # 将 API 日期覆盖写入（替换“日期：……”行）
                            md = re.sub(r"^日期：.*$", f"日期：{date_str}", md, flags=re.MULTILINE)
                        except Exception as exc:
                            log.warning("AIbase 日报详情失败: url=%s err=%s，使用简单摘要", detail_url, exc)
                            summary = _get_from_path(it, api_config.get("summary_path") or "description") or ""
                            md = f"# {title}\n\n来源：{detail_url}\n日期：{date_str}\n\n{summary}\n"

                        # 以日期为文件名（若同日多篇，追加自增序号）
                        base_name = f"daily-{date_str}.md"
                        out_path = os.path.join(output_dir, base_name)
                        if os.path.exists(out_path):
                            if not stop_on_duplicate:
                                k = 2
                                while True:
                                    alt = os.path.join(output_dir, f"daily-{date_str}_{k}.md")
                                    if not os.path.exists(alt):
                                        out_path = alt
                                        break
                                    k += 1
                            else:
                                stop_flag = True
                                break
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(md)
                        written.append(out_path)
                        log.info("AIbase 日报写入: %s", out_path)
                        # 记录本轮已写入的日期
                        written_dates.add(date_str)
                    if stop_flag:
                        break
                return written

        # HTML 回退：遍历页码：先尝试 ?page=，失败再尝试 /page/
        stop_flag = False
        for page_idx in range(1, max_pages + 1):
            if page_idx == 1:
                page_url = daily_url
            else:
                page_url = _build_url_with_param(daily_url, "page", page_idx)
            try:
                resp = http_get(session, page_url, headers=DEFAULT_HEADERS_HTML)
            except Exception:
                # 回退到 /page/N
                parsed = urlparse(daily_url)
                new_path = f"{parsed.path.rstrip('/')}/page/{page_idx}"
                page_url = urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))
                resp = http_get(session, page_url, headers=DEFAULT_HEADERS_HTML)

            log.info("AIbase 日报页面: page=%s status=%s url=%s", page_idx, resp.status_code, page_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            detail_links = _extract_daily_links(soup, daily_url)
            log.info("AIbase 日报列表: page=%s links=%s", page_idx, len(detail_links))

            if page_idx > 1 and not detail_links:
                log.info("AIbase 日报空页停止: page=%s url=%s", page_idx, page_url)
                break

            for detail_url in detail_links:
                # 重复检测（文件与本轮日期）
                u_hash = _url_hash(detail_url)
                try:
                    dr = http_get(session, detail_url, headers=DEFAULT_HEADERS_HTML)
                    dsoup = BeautifulSoup(dr.text, "html.parser")
                    md = _extract_article_markdown(dsoup, detail_url)
                    m = re.search(r"日期：([0-9]{4}-[0-9]{2}-[0-9]{2})", md)
                    date_in_md = m.group(1) if m else datetime.now().strftime("%Y-%m-%d")
                    # 若当日文件已存在（含旧目录）也视为重复并停止
                    legacy_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "data", "daily"))
                    if stop_on_duplicate and (os.path.exists(os.path.join(output_dir, f"{date_in_md}.md")) or os.path.exists(os.path.join(legacy_dir, f"{date_in_md}.md"))):
                        log.info("AIbase 日报命中已存在日期文件，停止继续分页: date=%s page=%s", date_in_md, page_idx)
                        stop_flag = True
                        break
                    # 本轮运行内若同日期已写过，也直接停止，不生成 _2 文件
                    if stop_on_duplicate and date_in_md in written_dates:
                        log.info("AIbase 日报本轮已写入同日期，停止继续分页: date=%s page=%s", date_in_md, page_idx)
                        stop_flag = True
                        break
                        base_name = f"daily-{date_in_md}.md"
                    out_path = os.path.join(output_dir, base_name)
                    if os.path.exists(out_path):
                            # 若不启用停止策略，才考虑生成 _2；默认 stop_on_duplicate=True 下不会走到这里
                            if not stop_on_duplicate:
                                k = 2
                                while True:
                                    alt = os.path.join(output_dir, f"daily-{date_in_md}_{k}.md")
                                    if not os.path.exists(alt):
                                        out_path = alt
                                        break
                                    k += 1
                            else:
                                # 安全保护：stop_on_duplicate=True 时不应生成 _2，直接停止
                                stop_flag = True
                                break
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(md)
                    written.append(out_path)
                    log.info("AIbase 日报写入: %s", out_path)
                    written_dates.add(date_in_md)
                except Exception as exc:
                    log.warning("AIbase 日报详情失败: url=%s err=%s", detail_url, exc)
            if stop_flag:
                break

    return written


