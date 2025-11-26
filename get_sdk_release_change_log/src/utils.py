"""工具函数：解析 GitHub URL 等。"""
import re
from typing import Optional


def parse_github_repo(url_or_repo: str) -> Optional[str]:
    """从 GitHub URL 或直接格式中提取 owner/repo 格式。

    支持的格式：
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    - owner/repo

    返回: owner/repo 格式，如果无法解析则返回 None
    """
    if not url_or_repo:
        return None

    # 如果已经是 owner/repo 格式
    if '/' in url_or_repo and not url_or_repo.startswith('http') and not url_or_repo.startswith('git@'):
        parts = url_or_repo.split('/')
        if len(parts) == 2:
            return url_or_repo

    # 匹配 https://github.com/owner/repo.git 或 https://github.com/owner/repo
    pattern = r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.search(pattern, url_or_repo)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return f"{owner}/{repo}"

    return None

