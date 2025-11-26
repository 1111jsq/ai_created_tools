from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict
import os

# 添加项目根目录到路径，以便导入 common.config_loader
# 从 src/config.py 向上查找：src -> get_agent_news -> 项目根目录
_current_file = Path(__file__).resolve()
# src/config.py 的父目录是 src/，再上一级是 get_agent_news/
_get_agent_news_dir = _current_file.parent.parent  # get_agent_news/
_project_root = _get_agent_news_dir.parent  # 项目根目录

# 使用绝对路径确保正确
_project_root_resolved = _project_root.resolve()
if str(_project_root_resolved) not in sys.path:
    sys.path.insert(0, str(_project_root_resolved))

from common.config_loader import get_env, load_env_config

# 确保加载 .env 文件
load_env_config()

# 使用 Path 对象确保路径正确（使用绝对路径）
# 优先从当前工作目录查找，因为用户可能从不同目录运行
import os
cwd = Path(os.getcwd()).resolve()

# 策略：优先使用当前工作目录（如果它是 get_agent_news 目录）
if (cwd / "configs" / "sources.yaml").exists():
    # 当前目录就是 get_agent_news
    _get_agent_news_dir_resolved = cwd
elif (cwd / "get_agent_news" / "configs" / "sources.yaml").exists():
    # 当前目录是项目根目录
    _get_agent_news_dir_resolved = cwd / "get_agent_news"
elif (_get_agent_news_dir.resolve() / "configs" / "sources.yaml").exists():
    # 从 __file__ 计算的路径正确
    _get_agent_news_dir_resolved = _get_agent_news_dir.resolve()
elif (_project_root_resolved / "get_agent_news" / "configs" / "sources.yaml").exists():
    # 从项目根目录查找
    _get_agent_news_dir_resolved = _project_root_resolved / "get_agent_news"
else:
    # 最后回退到从 __file__ 计算的路径
    _get_agent_news_dir_resolved = _get_agent_news_dir.resolve()

PROJECT_ROOT = _get_agent_news_dir_resolved
DEFAULT_SOURCES_PATH = str(PROJECT_ROOT / "configs" / "sources.yaml")
DEFAULT_LOG_PATH = str(PROJECT_ROOT / "logs" / "app.log")


def get_sources_path() -> str:
    """获取 sources.yaml 配置文件路径，确保返回绝对路径"""
    path = get_env("NEWS_SOURCES_PATH", DEFAULT_SOURCES_PATH)
    # 如果是相对路径，转换为绝对路径（相对于项目根目录）
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = PROJECT_ROOT / path_obj
    return str(path_obj.resolve())


def get_log_path() -> str:
    """获取日志文件路径，确保返回绝对路径"""
    path = get_env("NEWS_LOG_PATH", DEFAULT_LOG_PATH)
    # 如果是相对路径，转换为绝对路径（相对于项目根目录）
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = PROJECT_ROOT / path_obj
    return str(path_obj.resolve())


def get_deepseek_config() -> Dict[str, Any]:
    return {
        "api_key": get_env("LLM_API_KEY", ""),
        "base_url": get_env("LLM_BASE_URL", "https://api.deepseek.com"),
        "default_model": get_env("LLM_MODEL", "deepseek-chat"),
        "timeout": get_env("LLM_TIMEOUT", 60, int),
    }
