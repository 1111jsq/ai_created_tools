"""工具函数"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple


def parse_date(date_str: str) -> datetime:
    """解析日期字符串为 datetime 对象"""
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def format_yyyymmdd(dt: datetime) -> str:
    """格式化日期为 YYYYMMDD 格式"""
    return dt.strftime("%Y%m%d")


def derive_range(start: Optional[str], end: Optional[str], last_days: Optional[int]) -> Tuple[datetime, datetime]:
    """推导时间范围"""
    if start and end:
        s = parse_date(start)
        e = parse_date(end)
        if e < s:
            raise ValueError("end must be >= start")
        return s, e
    # 默认最近 7 天（含今天）
    days = last_days if (last_days and last_days > 0) else 7
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt = today - timedelta(days=days - 1)
    end_dt = today
    return start_dt, end_dt


def derive_label(start_dt: datetime, end_dt: datetime) -> str:
    """推导标签字符串"""
    return f"{format_yyyymmdd(start_dt)}-{format_yyyymmdd(end_dt)}"


def setup_logging(level: str) -> None:
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def parse_iso_flexible(s: str) -> Optional[datetime]:
    """灵活解析 ISO 格式的日期时间字符串"""
    if not s:
        return None
    # Try common formats
    candidates = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    # Handle 'Z' timezone
    ss = s.strip().replace("Z", "+0000").replace("+00:00", "+0000")
    for fmt in candidates:
        try:
            if "%z" in fmt:
                return datetime.strptime(ss, fmt)
            else:
                return datetime.strptime(ss, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def within_range(dt: Optional[datetime], start_dt: datetime, end_dt: datetime) -> bool:
    """判断日期是否在范围内"""
    if not dt:
        return False
    return start_dt <= dt.replace(tzinfo=timezone.utc) <= end_dt


def sanitize_mermaid_text(text: str) -> str:
    """清理 Mermaid 文本，移除括号类符号"""
    return re.sub(r"[()\\[\\]{}]", "", text or "")


def parse_label_to_range(label: str) -> Optional[Tuple[datetime, datetime]]:
    """解析标签字符串为时间范围"""
    # YYYYMMDD-YYYYMMDD
    m = re.match(r"^(\d{8})-(\d{8})$", label)
    if m:
        s = datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)
        e = datetime.strptime(m.group(2), "%Y%m%d").replace(tzinfo=timezone.utc)
        return (s, e) if e >= s else None
    # YYYY-MM monthly
    m2 = re.match(r"^(\d{4})-(\d{2})$", label)
    if m2:
        y, mo = int(m2.group(1)), int(m2.group(2))
        start = datetime(y, mo, 1, tzinfo=timezone.utc)
        if mo == 12:
            end = datetime(y + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
        else:
            end = datetime(y, mo + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
        return (start, end)
    return None


def ensure_dir(p: Path) -> None:
    """确保目录存在"""
    p.mkdir(parents=True, exist_ok=True)

