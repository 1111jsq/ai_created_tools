from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Tuple


def _parse_entry(filename: str) -> Tuple[str, str]:
	"""
	返回 (类型, 日期)；类型为 'daily' 或 'news'，否则返回 ('', '')
	"""
	if not filename.endswith(".md") or filename == "index.md":
		return ("", "")
	if filename.startswith("daily-"):
		# daily-YYYY-MM-DD.md
		parts = filename.split("-", 2)
		if len(parts) >= 3:
			return ("daily", parts[1] + "-" + parts[2].replace(".md", ""))
		return ("daily", filename.replace("daily-", "").replace(".md", ""))
	if filename.startswith("news-"):
		# news-YYYY-MM-DD-...
		try:
			date_part = filename.split("-", 3)[1:3]
			date_key = "-".join(date_part)
			return ("news", date_key)
		except Exception:
			return ("news", "")
	return ("", "")


def _scan_flat(content_root: str) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
	files = []
	try:
		files = sorted(os.listdir(content_root))
	except Exception:
		return ([], [])
	daily: List[Tuple[str, str]] = []
	news: List[Tuple[str, str]] = []
	for name in files:
		tp, date_key = _parse_entry(name)
		if not tp or not date_key:
			continue
		if tp == "daily":
			daily.append((date_key, name))
		elif tp == "news":
			news.append((date_key, name))
	return (daily, news)


def build_index(content_root: str, new_daily: int = 0, new_news: int = 0, params: Dict[str, str] | None = None) -> str:
	"""
	扫描 content_root 下的 daily 与 news，生成 index.md。
	"""
	os.makedirs(content_root, exist_ok=True)
	index_path = os.path.join(content_root, "index.md")

	daily, news = _scan_flat(content_root)

	params = params or {}
	now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

	lines: List[str] = []
	lines.append("# 本次运行摘要")
	lines.append("")
	lines.append(f"- 生成时间：{now}")
	lines.append(f"- 日报新增：{new_daily}")
	lines.append(f"- 资讯新增：{new_news}")
	if params:
		for k, v in params.items():
			lines.append(f"- {k}：{v}")
	lines.append("")

	lines.append("## 日报（按日期）")
	if not daily:
		lines.append("- 暂无")
	else:
		cur_date = None
		for date_key, relpath in daily:
			if date_key != cur_date:
				if cur_date is not None:
					lines.append("")
				lines.append(f"### {date_key}")
				cur_date = date_key
			lines.append(f"- [{relpath}]({relpath})")
	lines.append("")

	lines.append("## 资讯（按日期）")
	if not news:
		lines.append("- 暂无")
	else:
		cur_date = None
		for date_key, relpath in news:
			if date_key != cur_date:
				if cur_date is not None:
					lines.append("")
				lines.append(f"### {date_key}")
				cur_date = date_key
			lines.append(f"- [{relpath}]({relpath})")
	lines.append("")

	with open(index_path, "w", encoding="utf-8") as f:
		f.write("\n".join(lines))
	return index_path

