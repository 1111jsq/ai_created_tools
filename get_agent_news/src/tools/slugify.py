from __future__ import annotations

import re
from typing import Optional


_invalid = re.compile(r"[^a-z0-9\-]+")
_dash_multi = re.compile(r"-{2,}")


def slugify(title: Optional[str]) -> str:
	title = (title or "").strip().lower()
	if not title:
		return "untitled"
	title = re.sub(r"\s+", "-", title)
	title = _invalid.sub("-", title)
	title = _dash_multi.sub("-", title)
	return title.strip("-") or "untitled"

