from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass
class MonthWindow:
    month_str: str
    start: datetime
    end: datetime


def parse_month(month: str) -> MonthWindow:
    # month format: YYYY-MM
    start = datetime.strptime(month + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1, day=1)
    else:
        next_month = start.replace(month=start.month + 1, day=1)
    end = next_month - timedelta(seconds=1)
    return MonthWindow(month_str=month, start=start, end=end)


def parse_date(date_str: str) -> datetime:
    # date_str: YYYY-MM-DD
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def format_yyyymmdd(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def ensure_data_dirs(label: str) -> dict[str, Path]:
    # 统一输出到 get_paper/data，无论当前工作目录在哪
    # 本文件位于 get_paper/src/agents_papers/utils/dates.py
    # 上溯三层到 get_paper 目录：utils -> agents_papers -> src -> get_paper
    base = Path(__file__).resolve().parents[3] / "data"
    raw_dir = base / "raw" / label
    normalized_dir = base / "normalized" / label
    exports_dir = base / "exports" / label
    for d in (raw_dir, normalized_dir, exports_dir):
        d.mkdir(parents=True, exist_ok=True)
    return {
        "raw": raw_dir,
        "normalized": normalized_dir,
        "exports": exports_dir,
    }


def derive_label(month: str | None = None, start: datetime | None = None, end: datetime | None = None) -> str:
    if month:
        return month
    if start and end:
        return f"{format_yyyymmdd(start)}-{format_yyyymmdd(end)}"
    raise ValueError("either month or start+end must be provided")


