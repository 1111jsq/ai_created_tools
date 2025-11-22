from __future__ import annotations

import os
from datetime import datetime
from typing import Optional


def get_date_path(base_dir: str, date: Optional[datetime] = None, date_format: str = "%Y/%m/%d") -> str:
    """
    获取指定日期的目录路径
    
    Args:
        base_dir: 基础目录路径
        date: 日期，默认为今天
        date_format: 日期格式，默认 "%Y/%m/%d"
        
    Returns:
        完整的目录路径
    """
    if date is None:
        date = datetime.now()
    
    date_path = date.strftime(date_format)
    return os.path.join(base_dir, date_path)


def ensure_date_structure(base_dir: str, date: Optional[datetime] = None, date_format: str = "%Y/%m/%d") -> str:
    """
    确保日期分层目录结构存在
    
    Args:
        base_dir: 基础目录路径
        date: 日期，默认为今天
        date_format: 日期格式，默认 "%Y/%m/%d"
        
    Returns:
        创建的完整目录路径
    """
    full_path = get_date_path(base_dir, date, date_format)
    os.makedirs(full_path, exist_ok=True)
    return full_path



