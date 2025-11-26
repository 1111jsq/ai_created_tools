"""HTML 页面解析器"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from src.models import BlogPost
from src.parsers.markdown_converter import html_to_markdown

logger = logging.getLogger(__name__)


DEFAULT_HEADERS_HTML = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def fetch_html_list(
    url: str,
    source: str,
    selectors: Dict[str, str],
    pagination: Optional[Dict] = None,
    tags: List[str] = None,
    delay: float = 1.0,
    timeout: float = 30.0,
) -> List[BlogPost]:
    """从 HTML 列表页抓取文章链接
    
    Args:
        url: 列表页 URL
        source: 博客源名称
        selectors: 选择器配置
        pagination: 翻页配置
        tags: 标签列表
        delay: 请求延迟
        timeout: 请求超时
        
    Returns:
        BlogPost 列表（仅包含链接信息，需要后续抓取详情）
    """
    logger.info("开始抓取 HTML 列表页: %s", url)
    
    tags = tags or []
    pagination = pagination or {}
    max_pages = int(pagination.get("max_pages", 1) or 1)
    p_type = (pagination.get("type") or "").lower()
    
    posts = []
    seen_urls = set()
    
    with requests.Session() as session:
        current_url = url
        
        for page_idx in range(1, max_pages + 1):
            # 构建当前页 URL
            if p_type == "param":
                param_name = pagination.get("param_name", "page")
                start = int(pagination.get("start", 1) or 1)
                step = int(pagination.get("step", 1) or 1)
                page_value = start + (page_idx - 1) * step
                page_url = _build_url_with_param(url, param_name, page_value)
            elif p_type == "path":
                # 路径参数分页（如 /page/2, /page/3）
                path_template = pagination.get("path_template", "/page/{page}")
                start = int(pagination.get("start", 1) or 1)
                step = int(pagination.get("step", 1) or 1)
                page_value = start + (page_idx - 1) * step
                if page_idx == 1 and start == 1:
                    # 第一页使用原始 URL
                    page_url = url
                else:
                    # 其他页使用路径模板
                    parsed = urlparse(url)
                    # 如果路径模板是绝对路径（以 / 开头），直接使用它替换整个路径
                    if path_template.startswith("/"):
                        path = path_template.format(page=page_value)
                    else:
                        # 如果路径模板是相对路径，追加到基础路径
                        base_path = parsed.path.rstrip("/")  # 移除末尾的斜杠
                        path = f"{base_path}/{path_template.format(page=page_value)}"
                    # 确保路径以 / 开头
                    if not path.startswith("/"):
                        path = "/" + path
                    page_url = urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))
            else:
                page_url = current_url
            
            try:
                resp = session.get(page_url, headers=DEFAULT_HEADERS_HTML, timeout=timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # 提取文章项
                list_item_selector = selectors.get("list_item", "article")
                items = soup.select(list_item_selector)
                logger.info("页面 %s 找到 %s 个文章项", page_idx, len(items))
                
                page_posts = 0
                for item in items:
                    # 提取标题和链接
                    title_selector = selectors.get("title", "a")
                    link_selector = selectors.get("link", "a")
                    
                    # 如果 item 本身就是链接（如 list_item 是 a[href*="/news/"]），直接使用它
                    if item.name == "a" and item.get("href"):
                        title_el = item
                        link_el = item
                    else:
                        title_el = item.select_one(title_selector) if title_selector else item
                        link_el = item.select_one(link_selector) if link_selector else item
                    
                    if not title_el or not link_el:
                        continue
                    
                    title = title_el.get_text(strip=True)
                    link = link_el.get("href") or ""
                    
                    if not title or not link:
                        continue
                    
                    # 如果标题和链接是同一个元素，且标题文本包含日期/类别等额外信息，尝试提取纯标题
                    if title_el == link_el and title:
                        # 尝试从混在一起的文本中提取标题（例如：标题类别日期描述）
                        # 使用正则表达式匹配日期模式，提取日期之前的部分作为标题
                        import re
                        # 匹配日期模式：Month DD, YYYY 或类似格式
                        date_pattern = r'([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})'
                        date_match = re.search(date_pattern, title)
                        if date_match:
                            # 找到日期，提取日期之前的部分作为标题
                            title = title[:date_match.start()].strip()
                            # 移除可能的类别标签（如 Announcements, Product 等）
                            category_pattern = r'^(Announcements|Product|Policy|Economic Research|Research)\s*'
                            title = re.sub(category_pattern, '', title, flags=re.IGNORECASE).strip()
                        else:
                            # 如果没有日期，尝试移除常见的类别前缀
                            category_pattern = r'^(Announcements|Product|Policy|Economic Research|Research)\s+'
                            title = re.sub(category_pattern, '', title, flags=re.IGNORECASE).strip()
                        
                        # 如果标题仍然很长，可能包含描述，尝试截取第一句
                        if len(title) > 100:
                            # 尝试找到第一个句号或换行
                            first_sentence = re.split(r'[.\n]', title)[0]
                            if len(first_sentence) > 20:  # 如果第一句足够长，使用它
                                title = first_sentence.strip()
                    
                    # 处理相对链接
                    if not link.startswith(("http://", "https://")):
                        link = urljoin(page_url, link)
                    
                    if link in seen_urls:
                        continue
                    seen_urls.add(link)
                    
                    # 提取发布日期和作者（如果选择器存在）
                    published_at = None
                    if "date" in selectors:
                        date_el = item.select_one(selectors["date"])
                        if date_el:
                            date_text = date_el.get_text(strip=True) or date_el.get("datetime", "")
                            if date_text:
                                try:
                                    dt = date_parser.parse(date_text)
                                    published_at = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                                except Exception:
                                    pass
                    
                    # 如果日期选择器指向链接本身，尝试从链接文本中提取日期
                    if not published_at and title_el == link_el:
                        import re
                        date_pattern = r'([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})'
                        date_match = re.search(date_pattern, title_el.get_text(strip=True))
                        if date_match:
                            try:
                                dt = date_parser.parse(date_match.group(1))
                                published_at = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                            except Exception:
                                pass
                    
                    author = None
                    if "author" in selectors:
                        author_el = item.select_one(selectors["author"])
                        if author_el:
                            author = author_el.get_text(strip=True)
                    
                    post = BlogPost(
                        source=source,
                        title=title,
                        url=link,
                        published_at=published_at,
                        author=author,
                        tags=tags,
                    )
                    post.ensure_hash()
                    posts.append(post)
                    page_posts += 1
                
                if page_posts == 0:
                    logger.info("页面 %s 无新文章，停止翻页", page_idx)
                    break
                
                # 处理下一页（type=next）
                if p_type == "next":
                    next_selector = pagination.get("next_selector")
                    if next_selector:
                        next_el = soup.select_one(next_selector)
                        if next_el:
                            next_href = next_el.get("href")
                            if next_href:
                                current_url = urljoin(page_url, next_href)
                            else:
                                break
                        else:
                            break
                    else:
                        break
                
                # 延迟
                if page_idx < max_pages:
                    time.sleep(delay)
                    
            except Exception as exc:
                logger.exception("抓取页面 %s 失败: %s", page_idx, exc)
                break
    
    logger.info("HTML 列表页抓取完成，共 %s 篇文章", len(posts))
    return posts


def fetch_html_content(
    url: str,
    source: str,
    content_selectors: Dict[str, str],
    title: Optional[str] = None,
    tags: List[str] = None,
    timeout: float = 30.0,
) -> Optional[BlogPost]:
    """抓取文章详情页内容（带重试机制）
    
    Args:
        url: 文章 URL
        source: 博客源名称
        content_selectors: 内容选择器配置
        title: 文章标题（如果已知）
        tags: 标签列表
        timeout: 请求超时
        
    Returns:
        BlogPost 对象，如果抓取失败返回 None
    """
    logger.debug("抓取文章详情: %s", url)
    
    # 重试逻辑：最多尝试2次（初始1次 + 重试1次）
    max_attempts = 2
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            with requests.Session() as session:
                resp = session.get(url, headers=DEFAULT_HEADERS_HTML, timeout=timeout)
                
                # 对于 403 错误，也尝试重试
                if resp.status_code == 403:
                    if attempt < max_attempts:
                        logger.warning("访问被拒绝 (403): %s - 第 %s 次尝试，等待1秒后重试", url, attempt)
                        time.sleep(1.0)
                        continue
                    else:
                        logger.warning("访问被拒绝 (403): %s - 重试后仍失败，跳过此文章", url)
                        return None
                
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # 提取标题
                if not title and "title" in content_selectors:
                    title_el = soup.select_one(content_selectors["title"])
                    if title_el:
                        title = title_el.get_text(strip=True)
                
                if not title:
                    title = soup.find("title")
                    title = title.get_text(strip=True) if title else "Untitled"
                
                # 提取正文内容
                content_html = ""
                if "content" in content_selectors:
                    content_el = soup.select_one(content_selectors["content"])
                    if content_el:
                        content_html = str(content_el)
                else:
                    # 如果没有指定选择器，尝试提取 main 或 article 标签
                    content_el = soup.find("main") or soup.find("article")
                    if content_el:
                        content_html = str(content_el)
                
                if not content_html:
                    logger.warning("未找到文章内容: %s", url)
                    return None
                
                # 转换为 Markdown
                content_md = html_to_markdown(content_html, base_url=url)
                
                # 提取发布日期
                published_at = None
                if "date" in content_selectors:
                    date_el = soup.select_one(content_selectors["date"])
                    if date_el:
                        date_text = date_el.get_text(strip=True) or date_el.get("datetime", "")
                        if date_text:
                            try:
                                dt = date_parser.parse(date_text)
                                published_at = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                            except Exception:
                                pass
                
                # 提取作者
                author = None
                if "author" in content_selectors:
                    author_el = soup.select_one(content_selectors["author"])
                    if author_el:
                        author = author_el.get_text(strip=True)
                
                post = BlogPost(
                    source=source,
                    title=title,
                    url=url,
                    published_at=published_at,
                    author=author,
                    content=content_md,
                    tags=tags or [],
                )
                post.ensure_hash()
                return post
                
        except Exception as exc:
            last_exception = exc
            if attempt < max_attempts:
                logger.warning("抓取文章详情失败 (第 %s 次尝试): %s - %s，等待1秒后重试", attempt, url, exc)
                time.sleep(1.0)
            else:
                logger.error("抓取文章详情失败 (重试后仍失败): %s - %s", url, exc)
                return None
    
    # 如果所有尝试都失败，返回 None
    if last_exception:
        logger.error("抓取文章详情最终失败: %s - %s", url, last_exception)
    return None


def fetch_single_url(
    url: str,
    source: Optional[str] = None,
    tags: Optional[List[str]] = None,
    timeout: float = 30.0,
) -> Optional[BlogPost]:
    """智能抓取单个 URL 的页面内容（无需配置选择器）
    
    Args:
        url: 目标 URL
        source: 博客源名称（如果为 None，则从 URL 提取域名）
        tags: 标签列表（如果为 None，则从 URL 提取域名作为标签）
        timeout: 请求超时
        
    Returns:
        BlogPost 对象，如果抓取失败返回 None
    """
    logger.info("开始智能抓取单 URL: %s", url)
    
    # 从 URL 提取域名作为 source（如果没有提供）
    if not source:
        parsed = urlparse(url)
        source = parsed.netloc.replace("www.", "").split(".")[0] if parsed.netloc else "unknown"
    
    # 从 URL 提取标签（如果没有提供）
    if tags is None:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "") if parsed.netloc else ""
        tags = [domain] if domain else []
    
    # 重试逻辑：最多尝试2次（初始1次 + 重试1次）
    max_attempts = 2
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            with requests.Session() as session:
                resp = session.get(url, headers=DEFAULT_HEADERS_HTML, timeout=timeout)
                
                # 对于 403 错误，也尝试重试
                if resp.status_code == 403:
                    if attempt < max_attempts:
                        logger.warning("访问被拒绝 (403): %s - 第 %s 次尝试，等待1秒后重试", url, attempt)
                        time.sleep(1.0)
                        continue
                    else:
                        logger.warning("访问被拒绝 (403): %s - 重试后仍失败，跳过此文章", url)
                        return None
                
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
            
            # 智能提取标题：尝试多种选择器
            title = None
            title_selectors = [
                "h1",
                "title",
                "[role='heading']",
                ".post-title",
                ".article-title",
                ".entry-title",
            ]
            for selector in title_selectors:
                title_el = soup.select_one(selector)
                if title_el:
                    title = title_el.get_text(strip=True)
                    if title and len(title) > 5:  # 确保标题有意义
                        break
            
            # 如果还没找到，使用 title 标签
            if not title:
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    # 清理常见的标题后缀（如 " | Site Name"）
                    if " | " in title:
                        title = title.split(" | ")[0]
            
            if not title:
                title = "Untitled"
            
            # 智能提取正文内容：尝试多种选择器
            content_html = None
            content_selectors = [
                "main",
                "article",
                "[role='main']",
                ".content",
                ".post-content",
                ".article-content",
                ".entry-content",
                ".post-body",
                ".article-body",
                "#content",
                "#main-content",
            ]
            
            for selector in content_selectors:
                content_el = soup.select_one(selector)
                if content_el:
                    # 检查内容是否足够长（至少 200 字符）
                    text_content = content_el.get_text(strip=True)
                    if len(text_content) > 200:
                        content_html = str(content_el)
                        logger.debug("使用选择器找到内容: %s", selector)
                        break
            
            # 如果还没找到，尝试查找最大的包含文本的 div
            if not content_html:
                # 移除脚本、样式等
                for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    script.decompose()
                
                # 查找包含最多文本的 div
                divs = soup.find_all("div")
                best_div = None
                max_text_length = 0
                
                for div in divs:
                    text = div.get_text(strip=True)
                    if len(text) > max_text_length and len(text) > 200:
                        max_text_length = len(text)
                        best_div = div
                
                if best_div:
                    content_html = str(best_div)
                    logger.debug("使用最大文本 div 作为内容")
            
            if not content_html:
                logger.warning("未找到文章内容: %s", url)
                # 即使没有找到主要内容，也尝试提取 body 内容
                body = soup.find("body")
                if body:
                    # 移除脚本、样式等
                    for script in body(["script", "style", "nav", "header", "footer", "aside"]):
                        script.decompose()
                    content_html = str(body)
                    logger.debug("使用 body 作为内容")
                else:
                    return None
            
            # 转换为 Markdown
            content_md = html_to_markdown(content_html, base_url=url)
            
            # 智能提取发布日期：尝试多种选择器
            published_at = None
            date_selectors = [
                "time[datetime]",
                "time",
                "[itemprop='datePublished']",
                ".published",
                ".post-date",
                ".article-date",
                ".entry-date",
                "[class*='date']",
            ]
            
            for selector in date_selectors:
                date_el = soup.select_one(selector)
                if date_el:
                    date_text = date_el.get("datetime") or date_el.get_text(strip=True)
                    if date_text:
                        try:
                            dt = date_parser.parse(date_text)
                            published_at = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                            logger.debug("使用选择器找到日期: %s", selector)
                            break
                        except Exception:
                            continue
            
            # 智能提取作者：尝试多种选择器
            author = None
            author_selectors = [
                "[itemprop='author']",
                ".author",
                ".post-author",
                ".article-author",
                ".by-author",
                "[rel='author']",
            ]
            
            for selector in author_selectors:
                author_el = soup.select_one(selector)
                if author_el:
                    author = author_el.get_text(strip=True)
                    if author and len(author) > 0:
                        logger.debug("使用选择器找到作者: %s", selector)
                        break
            
            post = BlogPost(
                source=source,
                title=title,
                url=url,
                published_at=published_at,
                author=author,
                content=content_md,
                tags=tags,
            )
            post.ensure_hash()
            logger.info("成功抓取文章: %s", title)
            return post
                
        except Exception as exc:
            last_exception = exc
            if attempt < max_attempts:
                logger.warning("抓取单 URL 失败 (第 %s 次尝试): %s - %s，等待1秒后重试", attempt, url, exc)
                time.sleep(1.0)
            else:
                logger.error("抓取单 URL 失败 (重试后仍失败): %s - %s", url, exc)
                return None
    
    # 如果所有尝试都失败，返回 None
    if last_exception:
        logger.error("抓取单 URL 最终失败: %s - %s", url, last_exception)
    return None


def _build_url_with_param(base_url: str, param_name: str, param_value: int) -> str:
    """构建带查询参数的 URL"""
    parsed = urlparse(base_url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs[param_name] = [str(param_value)]
    new_query = urlencode(qs, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

