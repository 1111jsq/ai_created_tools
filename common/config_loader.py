"""
统一配置加载工具
从项目根目录的 .env 文件加载所有配置
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ImportError:
    # 如果没有安装 python-dotenv，使用空函数
    def load_dotenv(dotenv_path: Optional[str] = None) -> bool:
        return False


def find_project_root() -> Path:
    """查找项目根目录（包含 .env 文件或 .git 的目录）"""
    current = Path(__file__).resolve()
    
    # 从当前文件向上查找，直到找到包含 .env 或 .git 的目录
    for parent in [current.parent, *current.parents]:
        if (parent / '.env').exists() or (parent / '.git').exists() or (parent / '.env.example').exists():
            return parent
    
    # 如果找不到，返回当前文件的父目录的父目录（假设 common 在项目根目录下）
    return current.parent.parent


def load_env_config(dotenv_path: Optional[str] = None) -> bool:
    """
    加载 .env 配置文件
    
    Args:
        dotenv_path: .env 文件路径，如果为 None 则自动查找项目根目录的 .env 文件
    
    Returns:
        是否成功加载
    """
    if dotenv_path is None:
        project_root = find_project_root()
        dotenv_path = project_root / '.env'
        if not dotenv_path.exists():
            # 如果 .env 不存在，尝试查找 .env.example
            env_example = project_root / '.env.example'
            if env_example.exists():
                # 使用 logging 而不是 print，但避免在导入时初始化 logging
                try:
                    logging.warning(".env 文件不存在，请复制 .env.example 为 .env 并填写配置")
                except Exception:
                    # 如果 logging 未初始化，使用 print 作为后备
                    print("警告: .env 文件不存在，请复制 .env.example 为 .env 并填写配置")
            return False
    
    return load_dotenv(dotenv_path=str(dotenv_path), override=False)


def get_env(key: str, default: Any = None, type_func: type = str) -> Any:
    """
    获取环境变量，支持类型转换
    
    Args:
        key: 环境变量名
        default: 默认值
        type_func: 类型转换函数（str, int, float, bool）
    
    Returns:
        转换后的值
    """
    value = os.getenv(key, default)
    
    if value is None or value == default:
        return default
    
    if type_func == bool:
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    if type_func == int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    if type_func == float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    return value


# 自动加载 .env 文件（在导入时执行）
load_env_config()

