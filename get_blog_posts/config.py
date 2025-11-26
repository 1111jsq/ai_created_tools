"""配置管理"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径，以便导入 common.config_loader
_current_file = Path(__file__).resolve()
_get_blog_posts_dir = _current_file.parent  # get_blog_posts/
_project_root = _get_blog_posts_dir.parent  # 项目根目录

# 使用绝对路径确保正确
_project_root_resolved = _project_root.resolve()
if str(_project_root_resolved) not in sys.path:
    sys.path.insert(0, str(_project_root_resolved))

from common.config_loader import find_project_root, get_env


def get_config_path() -> Path:
    """获取配置文件路径"""
    current_file = Path(__file__).resolve()
    config_dir = current_file.parent / "configs"
    return config_dir / "blogs.yaml"


def get_output_dir() -> Path:
    """获取输出目录路径"""
    current_file = Path(__file__).resolve()
    output_dir = current_file.parent / "data" / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_log_path() -> str:
    """获取日志文件路径"""
    current_file = Path(__file__).resolve()
    log_dir = current_file.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir / "app.log")

