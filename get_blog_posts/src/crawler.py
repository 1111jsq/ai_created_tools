"""核心爬虫逻辑"""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import requests

from src.models import BlogPost, compute_url_hash
from src.parsers.html_parser import fetch_html_list, fetch_html_content
from src.parsers.rss_parser import fetch_rss_feed

logger = logging.getLogger(__name__)


def check_robots_txt(url: str, user_agent: str = "get_blog_posts/0.1") -> bool:
    """检查 robots.txt 是否允许访问
    
    Args:
        url: 目标 URL
        user_agent: User-Agent 字符串
        
    Returns:
        如果允许访问返回 True，否则返回 False
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        resp = requests.get(robots_url, timeout=10.0)
        if resp.status_code != 200:
            # robots.txt 不存在，默认允许
            return True
        
        # 简单的 robots.txt 解析（仅检查 Disallow）
        # 注意：这里只做简单检查，完整实现需要使用 urllib.robotparser
        content = resp.text.lower()
        user_agent_pattern = f"user-agent: {user_agent.lower()}"
        
        # 查找对应的 User-Agent 规则
        lines = content.split("\n")
        in_user_agent_section = False
        
        for line in lines:
            line = line.strip()
            if line.startswith("user-agent:"):
                in_user_agent_section = user_agent_pattern in line.lower() or "*" in line.lower()
            elif in_user_agent_section and line.startswith("disallow:"):
                disallow_path = line.split(":", 1)[1].strip()
                if disallow_path == "/":
                    return False
                if disallow_path and parsed.path.startswith(disallow_path):
                    return False
        
        return True
        
    except Exception as exc:
        logger.warning("检查 robots.txt 失败，默认允许: %s", exc)
        return True


class BlogCrawler:
    """博客爬虫"""
    
    def __init__(
        self,
        source: str,
        url: str,
        config: Dict,
        existing_url_hashes: Optional[Set[str]] = None,
    ):
        self.source = source
        self.url = url
        self.config = config
        self.existing_url_hashes = existing_url_hashes or set()
        self.crawled_posts: List[BlogPost] = []
    
    def crawl(self) -> List[BlogPost]:
        """执行爬取
        
        Returns:
            抓取到的博客文章列表
        """
        logger.info("开始爬取博客源: %s (%s)", self.source, self.url)
        
        # 检查 robots.txt
        if not check_robots_txt(self.url):
            logger.warning("robots.txt 禁止访问，跳过: %s", self.source)
            return []
        
        # 确定爬取方式
        blog_type = (self.config.get("type") or "html").lower()
        rss_url = self.config.get("rss_url")
        
        # 优先使用 RSS
        if blog_type == "rss" or rss_url:
            try:
                posts = list(fetch_rss_feed(
                    rss_url or self.url,
                    source=self.source,
                    base_url=self.url,
                    tags=self.config.get("tags", []),
                    timeout=self.config.get("timeout", 30.0),
                ))
                
                # 如果 RSS 中没有完整内容，需要抓取详情页
                posts_with_content = []
                for post in posts:
                    if not post.content or len(post.content.strip()) < 100:
                        # 需要抓取详情页
                        content_post = self._fetch_post_content(post)
                        if content_post:
                            posts_with_content.append(content_post)
                        else:
                            posts_with_content.append(post)
                    else:
                        posts_with_content.append(post)
                
                self.crawled_posts = self._filter_existing(posts_with_content)
                return self.crawled_posts
                
            except Exception as exc:
                logger.exception("RSS 抓取失败，尝试 HTML 模式: %s", exc)
                # 降级到 HTML 模式
                blog_type = "html"
        
        # HTML 模式
        if blog_type == "html":
            try:
                # 抓取列表页
                list_posts = fetch_html_list(
                    url=self.url,
                    source=self.source,
                    selectors=self.config.get("selectors", {}),
                    pagination=self.config.get("pagination", {}),
                    tags=self.config.get("tags", []),
                    delay=self.config.get("delay", 1.0),
                    timeout=self.config.get("timeout", 30.0),
                )
                
                # 抓取每篇文章的详情
                posts_with_content = []
                for post in list_posts:
                    # 检查是否已存在
                    if post.url_hash in self.existing_url_hashes:
                        logger.debug("文章已存在，跳过: %s", post.url)
                        continue
                    
                    # 抓取详情
                    content_post = self._fetch_post_content(post)
                    if content_post:
                        posts_with_content.append(content_post)
                    else:
                        # 如果详情抓取失败，保留列表页信息
                        posts_with_content.append(post)
                    
                    # 延迟
                    time.sleep(self.config.get("delay", 1.0))
                
                self.crawled_posts = posts_with_content
                return self.crawled_posts
                
            except Exception as exc:
                logger.exception("HTML 抓取失败: %s", exc)
                return []
        
        return []
    
    def _fetch_post_content(self, post: BlogPost) -> Optional[BlogPost]:
        """抓取文章详情内容"""
        content_selectors = self.config.get("content_selectors", {})
        if not content_selectors:
            # 如果没有配置详情页选择器，返回原 post
            return post
        
        try:
            content_post = fetch_html_content(
                url=post.url,
                source=post.source,
                content_selectors=content_selectors,
                title=post.title,
                tags=post.tags,
                timeout=self.config.get("timeout", 30.0),
            )
            return content_post
        except Exception as exc:
            logger.warning("抓取文章详情失败: %s, %s", post.url, exc)
            return post
    
    def _filter_existing(self, posts: List[BlogPost]) -> List[BlogPost]:
        """过滤已存在的文章"""
        if not self.existing_url_hashes:
            return posts
        
        filtered = []
        for post in posts:
            if post.url_hash not in self.existing_url_hashes:
                filtered.append(post)
            else:
                logger.debug("文章已存在，跳过: %s", post.url)
        
        return filtered

