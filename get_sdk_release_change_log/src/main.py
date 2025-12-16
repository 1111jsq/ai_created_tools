from __future__ import annotations
"""项目主入口：爬取 GitHub Releases 并生成总结。"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import yaml

# 自动检测并添加正确的项目路径到 sys.path
def setup_path():
    """自动检测项目目录并添加到 sys.path，支持从项目根目录或子目录运行。"""
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent.parent
    
    # 如果在项目根目录（有 get_sdk_release_change_log 子目录）
    if (current_dir / 'get_sdk_release_change_log' / 'config.py').exists():
        project_dir = current_dir / 'get_sdk_release_change_log'
        # 添加项目目录到路径
        if str(project_dir) not in sys.path:
            sys.path.insert(0, str(project_dir))
        # 切换到项目目录（这样相对路径的配置文件等才能正确找到）
        os.chdir(project_dir)
    # 如果已经在子目录（有 config.py）
    elif (current_dir / 'config.py').exists():
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
    # 如果都不存在，尝试使用脚本所在目录
    elif (script_dir / 'config.py').exists():
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        os.chdir(script_dir)

setup_path()

from config import PROJECT_PATHS, ENCODING, REPOSITORIES_CONFIG_FILE, SUMMARY_CONFIG
from src.crawler import GithubReleasesCrawler
from src.llm_client import DeepSeekClient
from src.utils import parse_github_repo


def ensure_dirs() -> None:
    """确保数据目录存在。"""
    os.makedirs(PROJECT_PATHS['releases_dir'], exist_ok=True)
    os.makedirs(PROJECT_PATHS['summaries_dir'], exist_ok=True)


def run(repo: str, max_pages: int, model: Optional[str], gh_token: Optional[str], start_page: int = 1, enable_summary: Optional[bool] = None) -> None:
    """执行抓取与总结流程。

    - repo: 目标 GitHub 仓库，如 "openai/openai-python"
    - max_pages: 最多抓取页数
    - model: LLM 模型名称
    - gh_token: GitHub 访问令牌
    - enable_summary: 是否启用总结功能（None 时使用全局配置）
    """
    crawler = GithubReleasesCrawler(repo=repo, token=gh_token)
    llm = DeepSeekClient(model=model)
    
    # 确定是否启用总结功能
    should_summarize = enable_summary if enable_summary is not None else SUMMARY_CONFIG.get('enable_summary', True)
    # 如果启用总结但 LLM 不可用，则禁用总结
    if should_summarize and not llm.available():
        logger.warning("总结功能已启用但 LLM 不可用（未配置 API Key），将跳过总结")
        should_summarize = False

    # 按页抓取 -> 每页一个 markdown 与一个总结
    for page in range(start_page, max_pages + start_page):
        items = crawler.fetch_releases_page(page)
        if not items:
            break
        md_path = crawler.save_page_markdown(page, items)
        logger.info("保存(页): %s", md_path)
        
        # 如果未启用总结功能，跳过总结步骤
        if not should_summarize:
            logger.info("总结功能已禁用，跳过总结: 页 %s", page)
            continue
            
        with open(md_path, 'r', encoding=ENCODING) as f:
            content = f.read()
        repo_slug = repo.replace('/', '_')
        sum_path = os.path.join(PROJECT_PATHS['summaries_dir'], f"{repo_slug}_{page}_summary.md")
        if os.path.exists(sum_path) and os.path.getsize(sum_path) > 0:
            logger.info("已存在总结(页)，跳过: %s", sum_path)
            continue
        
        # 分段摘要 + 汇总，避免上下文超限；将分段与汇总一并写入
        try:
            chunk_summaries = llm.summarize_long(content)
            if not chunk_summaries:
                logger.warning("页 %s 的分段摘要结果为空，跳过总结", page)
                continue
            
            final_summary = llm.summarize_aggregate(chunk_summaries)
            if not final_summary:
                logger.warning("页 %s 的最终汇总结果为空，跳过总结", page)
                continue
            
            with open(sum_path, 'w', encoding=ENCODING) as sf:
                sf.write("# 分段摘要\n\n")
                for i, cs in enumerate(chunk_summaries, start=1):
                    sf.write(f"## 段 {i}\n\n{cs}\n\n")
                sf.write("\n# 最终汇总\n\n")
                sf.write(final_summary)
            logger.info("总结(页): %s", sum_path)
        except Exception as e:
            logger.exception("页 %s 总结失败: %s", page, str(e))
            continue


def setup_logging() -> None:
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )


logger = logging.getLogger("sdk_release_crawler")


def load_repositories_config(config_path: str) -> List[Dict[str, Any]]:
    """从 YAML 配置文件加载仓库列表。

    返回: 仓库配置列表，每个元素包含 url, name, enabled, max_pages, start_page 等
    """
    if not os.path.exists(config_path):
        logger.warning("配置文件不存在: %s", config_path)
        return []

    with open(config_path, 'r', encoding=ENCODING) as f:
        data = yaml.safe_load(f)

    repositories = data.get('repositories', [])
    result = []
    for repo_config in repositories:
        if not isinstance(repo_config, dict):
            continue
        if not repo_config.get('enabled', True):
            continue

        url = repo_config.get('url', '')
        repo = parse_github_repo(url)
        if not repo:
            logger.warning("无法解析仓库 URL: %s", url)
            continue

        result.append({
            'repo': repo,
            'name': repo_config.get('name', repo),
            'url': url,
            'max_pages': repo_config.get('max_pages', 2),
            'start_page': repo_config.get('start_page', 1),
            'enable_summary': repo_config.get('enable_summary', None),  # None 表示使用全局配置
        })

    return result


def run_batch(repositories: List[Dict[str, Any]], model: Optional[str], gh_token: Optional[str]) -> None:
    """批量处理多个仓库。

    - repositories: 仓库配置列表
    - model: LLM 模型名称
    - gh_token: GitHub 访问令牌
    """
    total = len(repositories)
    for idx, repo_config in enumerate(repositories, start=1):
        repo = repo_config['repo']
        name = repo_config['name']
        max_pages = repo_config['max_pages']
        start_page = repo_config['start_page']
        enable_summary = repo_config.get('enable_summary', None)

        logger.info("[%s/%s] 开始处理: %s (%s)", idx, total, name, repo)
        try:
            run(repo=repo, max_pages=max_pages, model=model, gh_token=gh_token, start_page=start_page, enable_summary=enable_summary)
            logger.info("[%s/%s] 完成处理: %s (%s)", idx, total, name, repo)
        except Exception as e:
            logger.exception("[%s/%s] 处理失败: %s (%s)", idx, total, name, repo)
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Releases 爬虫与总结")
    parser.add_argument('--repo', type=str, default=None,
                        help='GitHub 仓库名或 URL，例如: langchain-ai/langchain 或 https://github.com/langchain-ai/langchain.git')
    parser.add_argument('--config', type=str, default=REPOSITORIES_CONFIG_FILE,
                        help=f'仓库配置文件路径（默认: {REPOSITORIES_CONFIG_FILE}）')
    parser.add_argument('--max-pages', type=int, default=2, help='最多抓取的页数（单仓库模式）')
    parser.add_argument('--start-page', type=int, default=1, help='起始页（默认 1，单仓库模式）')
    parser.add_argument('--model', type=str, default='deepseek-chat', help='大模型名称，默认 deepseek-chat，可设为 deepseek-reasoner')
    parser.add_argument('--gh-token', type=str, default=os.getenv('GITHUB_TOKEN','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'),
                        help='GitHub 访问令牌，可提升限额；可用环境变量 GITHUB_TOKEN 提供')
    parser.add_argument('--enable-summary', type=lambda x: x.lower() in ('true', '1', 'yes'), default=None,
                        help='是否启用总结功能（默认从配置文件读取，True/False）')
    args = parser.parse_args()
    print(args)

    setup_logging()
    ensure_dirs()
    logger.info("args: %s", args)
    # 如果指定了 --repo，使用单仓库模式（向后兼容）
    if args.repo:
        repo = parse_github_repo(args.repo)
        if not repo:
            logger.error("无法解析仓库: %s", args.repo)
            exit(1)
        enable_summary = args.enable_summary if args.enable_summary is not None else SUMMARY_CONFIG.get('enable_summary', True)
        run(repo=repo, max_pages=args.max_pages, model=args.model, gh_token=args.gh_token, start_page=args.start_page, enable_summary=enable_summary)
    else:
        # 否则从配置文件读取多个仓库
        repositories = load_repositories_config(args.config)
        if not repositories:
            logger.error("未找到可用的仓库配置，请使用 --repo 指定单个仓库或检查配置文件")
            exit(1)
        logger.info("从配置文件加载了 %s 个仓库", len(repositories))
        run_batch(repositories=repositories, model=args.model, gh_token=args.gh_token)


