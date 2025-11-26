from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List

from agents_papers.models.paper import Paper


def _parse_year_month(published: str | None, fallback_month: str | None) -> tuple[int | None, int | None]:
    if published:
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            return dt.year, dt.month
        except Exception:
            pass
    if fallback_month:
        try:
            year, month = fallback_month.split("-")
            return int(year), int(month)
        except Exception:
            return None, None
    return None, None


def normalize_records(entries: Iterable[Dict[str, Any]], month: str, start_date: str | None = None, end_date: str | None = None) -> List[Paper]:
    papers: List[Paper] = []
    for e in entries:
        if e.get("source") == "arxiv":
            year, mon = _parse_year_month(e.get("published"), month)
            # If explicit start/end date provided, filter by them, else fallback to month match
            if start_date and end_date and e.get("published"):
                try:
                    pub = datetime.fromisoformat(e["published"].replace("Z", "+00:00"))
                    if not (start_date <= pub.strftime("%Y-%m-%d") <= end_date):
                        continue
                except Exception:
                    pass
            else:
                if year and mon:
                    ym = f"{year:04d}-{mon:02d}"
                    if ym != month:
                        continue
            paper = Paper.from_minimal(
                title=e.get("title") or "",
                authors=e.get("authors") or [],
                abstract=e.get("abstract") or "",
                venue="arXiv",
                year=year,
                month=mon,
                primaryUrl=e.get("primaryUrl"),
                pdfUrl=e.get("pdfUrl"),
                sources=["arxiv"],
                doi=None,
                arxiv_id=e.get("arxiv_id"),
            )
            # Carry over coarse topics from categories
            cats = set((e.get("categories") or []))
            mapped_topics: List[str] = []
            if any(c.startswith("cs.AI") for c in cats):
                mapped_topics.append("cs.AI")
            if any(c.startswith("cs.LG") for c in cats):
                mapped_topics.append("cs.LG")
            if any(c.startswith("cs.MA") for c in cats):
                mapped_topics.append("cs.MA")
            paper.topics = sorted(set(mapped_topics))
            papers.append(paper)
    return papers


