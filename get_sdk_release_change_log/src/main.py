from __future__ import annotations
"""项目主入口：爬取 GitHub Releases 并生成总结。"""
import argparse
import os
from typing import Optional
from datetime import datetime

from config import PROJECT_PATHS, ENCODING
from src.crawler import GithubReleasesCrawler
from src.llm_client import DeepSeekClient


def ensure_dirs() -> None:
    """确保数据目录存在。"""
    os.makedirs(PROJECT_PATHS['releases_dir'], exist_ok=True)
    os.makedirs(PROJECT_PATHS['summaries_dir'], exist_ok=True)


def run(repo: str, max_pages: int, model: Optional[str], gh_token: Optional[str], start_page: int = 1) -> None:
    """执行抓取与总结流程。

    - repo: 目标 GitHub 仓库，如 "openai/openai-python"
    - max_pages: 最多抓取页数
    - model: LLM 模型名称
    - gh_token: GitHub 访问令牌
    """
    crawler = GithubReleasesCrawler(repo=repo, token=gh_token)
    llm = DeepSeekClient(model=model)

    # 按页抓取 -> 每页一个 markdown 与一个总结
    for page in range(start_page, max_pages + start_page):
        items = crawler.fetch_releases_page(page)
        if not items:
            break
        md_path = crawler.save_page_markdown(page, items)
        log(f"保存(页): {md_path}")
        with open(md_path, 'r', encoding=ENCODING) as f:
            content = f.read()
        repo_slug = repo.replace('/', '_')
        sum_path = os.path.join(PROJECT_PATHS['summaries_dir'], f"{repo_slug}_{page}_summary.md")
        if os.path.exists(sum_path) and os.path.getsize(sum_path) > 0:
            log(f"已存在总结(页)，跳过: {sum_path}")
            continue
        # 分段摘要 + 汇总，避免上下文超限；将分段与汇总一并写入
        chunk_summaries = llm.summarize_long(content)
        final_summary = llm.summarize_aggregate(chunk_summaries)
        with open(sum_path, 'w', encoding=ENCODING) as sf:
            sf.write("# 分段摘要\n\n")
            for i, cs in enumerate(chunk_summaries, start=1):
                sf.write(f"## 段 {i}\n\n{cs}\n\n")
            sf.write("\n# 最终汇总\n\n")
            sf.write(final_summary)
        log(f"总结(页): {sum_path}")


def log(message: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Releases 爬虫与总结")
    parser.add_argument('--repo', required=True, help='GitHub 仓库名，例如: langchain-ai/langchain')
    parser.add_argument('--max-pages', type=int, default=2, help='最多抓取的页数')
    parser.add_argument('--start-page', type=int, default=1, help='起始页（默认 1）')
    parser.add_argument('--model', type=str, default=None, help='大模型名称，默认 deepseek-chat，可设为 deepseek-reasoner')
    parser.add_argument('--gh-token', type=str, default=os.getenv('GITHUB_TOKEN'),
                        help='GitHub 访问令牌，可提升限额；可用环境变量 GITHUB_TOKEN 提供')
    args = parser.parse_args()

    ensure_dirs()
    run(repo=args.repo, max_pages=args.max_pages, model=args.model, gh_token=args.gh_token, start_page=args.start_page)


