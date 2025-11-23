"""子进程运行模块"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def run_subprocess(
    args: List[str],
    logger: logging.Logger,
    env: Optional[Dict[str, str]] = None,
) -> int:
    """运行子进程命令"""
    logger.info("执行命令: %s", " ".join(args))
    try:
        # 设置环境变量，确保子进程使用 UTF-8 编码
        process_env = {**os.environ, **(env or {})}
        process_env['PYTHONIOENCODING'] = 'utf-8'
        
        # 使用 UTF-8 编码，并设置错误处理策略
        cp = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # 遇到无法解码的字符时替换为占位符，而不是抛出异常
            env=process_env
        )
        if cp.stdout:
            logger.info("stdout:\n%s", cp.stdout.strip())
        if cp.stderr:
            logger.info("stderr:\n%s", cp.stderr.strip())
        if cp.returncode != 0:
            logger.warning("命令返回非零状态: %s", cp.returncode)
        return cp.returncode
    except Exception as e:
        logger.exception("命令执行失败: %s", e)
        return 2


def run_get_paper(start_dt: datetime, end_dt: datetime, logger: logging.Logger) -> None:
    """运行 get_paper 模块"""
    script = str(Path("get_paper") / "src" / "monthly_run.py")
    cmd = [sys.executable, script, "--start", start_dt.strftime("%Y-%m-%d"), "--end", end_dt.strftime("%Y-%m-%d")]
    run_subprocess(cmd, logger)


def run_get_agent_news(news_since_days: int, logger: logging.Logger) -> None:
    """运行 get_agent_news 模块"""
    script = str(Path("get_agent_news") / "src" / "main.py")
    cmd = [sys.executable, script, "--once", "--source", "all", "--news-since-days", str(news_since_days), "--export-markdown"]
    run_subprocess(cmd, logger)


def run_sdk_release_change_log(
    repos: List[str],
    start_page: int,
    max_pages: int,
    logger: logging.Logger,
) -> None:
    """运行 get_sdk_release_change_log 模块"""
    for repo in repos:
        repo = repo.strip()
        if not repo:
            continue
        script = str(Path("get_sdk_release_change_log") / "src" / "main.py")
        cmd = [sys.executable, script, "--repo", repo, "--start-page", str(start_page), "--max-pages", str(max_pages)]
        run_subprocess(cmd, logger)

