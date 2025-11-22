from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from src.models import NewsItem
from src.tools.slugify import slugify


def _ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


def export_news_item_markdown(item: NewsItem, base_dir: str = os.path.join("content")) -> str:
	"""
	将单条资讯以 Markdown 形式写入：content/news-YYYY-MM-DD-<slug>-<hash8>.md
	若标题为空则使用 news-<hash8>.md。
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

