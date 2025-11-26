from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from src.models import NewsItem
from src.tools.slugify import slugify
from src.tools.date_structure import ensure_date_structure


def _ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


def _generate_item_markdown(item: NewsItem) -> str:
	"""生成单个新闻项的 Markdown 内容"""
	lines = []
	lines.append(f"## {item.title or '资讯'}")
	lines.append("")
	
	if item.published_at:
		lines.append(f"**发布时间**: {item.published_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
	
	lines.append(f"**来源**: {item.source}")
	lines.append(f"**类型**: {item.source_type}")
	
	if item.tags:
		lines.append(f"**标签**: {', '.join(item.tags)}")
	
	lines.append(f"**抓取时间**: {item.fetched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
	lines.append("")
	
	lines.append(f"**原文链接**: [{item.url}]({item.url})")
	lines.append("")
	
	if item.summary:
		lines.append("### 摘要")
		lines.append("")
		lines.append(item.summary)
		lines.append("")
	
	return "\n".join(lines)


def export_news_items_by_date(items: List[NewsItem], base_dir: str = os.path.join("content")) -> List[str]:
	"""
	按日期将多条资讯合并导出到 Markdown 文件：content/news/YYYY/MM/DD.md
	同一天的新闻会合并到一个文件中。
	"""
	_ensure_dir(base_dir)
	
	# 按日期分组
	items_by_date = defaultdict(list)
	for item in items:
		date_obj = (item.published_at or item.fetched_at or datetime.utcnow()).date()
		items_by_date[date_obj].append(item)
	
	# 为每个日期创建文件
	exported_paths = []
	for date_obj, date_items in items_by_date.items():
		# 创建日期目录结构
		date_dir = ensure_date_structure(
			os.path.join(base_dir, "news"),
			datetime.combine(date_obj, datetime.min.time()),
			"%Y/%m/%d"
		)
		
		# 文件名：YYYY-MM-DD.md
		filename = f"{date_obj.isoformat()}.md"
		file_path = os.path.join(date_dir, filename)
		
		# 生成 Markdown 内容
		lines = [f"# {date_obj.isoformat()} 资讯", ""]
		
		for idx, item in enumerate(date_items, 1):
			lines.append(_generate_item_markdown(item))
			if idx < len(date_items):
				lines.append("---")
				lines.append("")
		
		# 写入文件
		with open(file_path, "w", encoding="utf-8") as f:
			f.write("\n".join(lines))
		
		exported_paths.append(file_path)
	
	return exported_paths


def export_news_item_markdown(item: NewsItem, base_dir: str = os.path.join("content")) -> str:
	"""
	将单条资讯以 Markdown 形式写入（已废弃，保留用于兼容性）。
	建议使用 export_news_items_by_date 批量导出。
	"""
	_ensure_dir(base_dir)
	date_str = (item.published_at or item.fetched_at or datetime.utcnow()).date().isoformat()
	slug = slugify(item.title)
	oid_suffix = (item.url_hash or "").strip()[:8] if item.url_hash else ""
	if slug != "untitled" and oid_suffix:
		filename = f"news-{date_str}-{slug}-{oid_suffix}.md"
	elif oid_suffix:
		filename = f"news-{date_str}-{oid_suffix}.md"
	else:
		filename = f"news-{date_str}-{slug}.md"
	out_path = os.path.join(base_dir, filename)

	lines = [
		f"# {item.title or '资讯'}",
		"",
		f"来源：{item.url}",
		f"发布时间：{item.published_at.isoformat() if item.published_at else ''}",
		"",
		(item.summary or "").strip(),
		"",
	]
	with open(out_path, "w", encoding="utf-8") as f:
		f.write("\n".join(lines))
	return out_path

