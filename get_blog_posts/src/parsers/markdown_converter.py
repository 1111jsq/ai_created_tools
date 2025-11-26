"""HTML 转 Markdown 转换器"""
from __future__ import annotations

import html2text
from typing import Optional
from urllib.parse import urljoin, urlparse


def html_to_markdown(html: str, base_url: Optional[str] = None) -> str:
    """将 HTML 转换为 Markdown
    
    Args:
        html: HTML 内容
        base_url: 基础 URL（用于处理相对链接）
        
    Returns:
        Markdown 格式的内容
    """
    if not html:
        return ""
    
    # 配置 html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # 不自动换行
    h.unicode_snob = True
    h.skip_internal_links = False
    h.inline_links = True
    h.wrap_links = False
    
    # 转换
    markdown = h.handle(html)
    
    # 处理相对链接（如果提供了 base_url）
    if base_url:
        markdown = _convert_relative_links(markdown, base_url)
    
    # 清理多余的空白
    markdown = _clean_whitespace(markdown)
    
    return markdown


def _convert_relative_links(markdown: str, base_url: str) -> str:
    """将 Markdown 中的相对链接转换为绝对链接"""
    lines = markdown.split("\n")
    result = []
    
    for line in lines:
        # 处理链接格式: [text](url)
        import re
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        def replace_link(match):
            text = match.group(1)
            url = match.group(2)
            # 如果是相对链接，转换为绝对链接
            if url and not url.startswith(("http://", "https://", "mailto:", "#")):
                url = urljoin(base_url, url)
            return f"[{text}]({url})"
        
        line = re.sub(link_pattern, replace_link, line)
        result.append(line)
    
    return "\n".join(result)


def _clean_whitespace(text: str) -> str:
    """清理多余的空白"""
    # 移除行尾空白
    lines = [line.rstrip() for line in text.split("\n")]
    # 合并多个空行（最多保留两个连续空行）
    result = []
    prev_empty = False
    for line in lines:
        is_empty = not line.strip()
        if is_empty and prev_empty:
            continue
        result.append(line)
        prev_empty = is_empty
    
    return "\n".join(result).strip()

