from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import feedparser

from agents_papers.utils.dates import format_yyyymmdd


logger = logging.getLogger(__name__)

ARXIV_API = "https://export.arxiv.org/api/query"


def _quote(term: str) -> str:
	term = term.strip()
	if " " in term and not (term.startswith('"') and term.endswith('"')):
		return f'"{term}"'
	return term


def _year_range_yyyymmdd(year: int) -> Tuple[str, str]:
	start = datetime(year, 1, 1, tzinfo=timezone.utc)
	end = datetime(year, 12, 31, tzinfo=timezone.utc)
	return format_yyyymmdd(start), format_yyyymmdd(end)


def build_survey_query(
	year: int,
	categories: Optional[List[str]] = None,
) -> str:
	# Survey and topic terms
	survey_terms = [_quote(t) for t in ["survey", "review"]]
	topic_terms = [_quote(t) for t in ["large language model", "LLM", "agent", "agents", "multi-agent", "agentic"]]
	survey_clause = " OR ".join([f"ti:{t}" for t in survey_terms] + [f"abs:{t}" for t in survey_terms])
	topic_clause = " OR ".join([f"ti:{t}" for t in topic_terms] + [f"abs:{t}" for t in topic_terms])

	# Categories
	cats = categories or ["cs.AI", "cs.LG", "cs.MA"]
	cat_clause = " OR ".join([f"cat:{c}" for c in cats])

	# Year window on submittedDate
	s, e = _year_range_yyyymmdd(year)
	date_clause = f"submittedDate:[{s} TO {e}]"

	parts = [f"({survey_clause})", f"({topic_clause})", f"({cat_clause})", date_clause]
	return " AND ".join(parts)


async def _fetch_page(client: httpx.AsyncClient, query: str, start: int, max_results: int) -> str:
	params = {
		"search_query": query,
		"start": start,
		"max_results": max_results,
		"sortBy": "submittedDate",
		"sortOrder": "descending",
	}
	resp = await client.get(ARXIV_API, params=params, timeout=30)
	resp.raise_for_status()
	return resp.text


def _extract_arxiv_id(entry_id: str) -> str:
	# entry_id example: 'http://arxiv.org/abs/2501.01234v1'
	if "/abs/" in entry_id:
		return entry_id.split("/abs/")[-1]
	return entry_id


def _parse_entries(xml_text: str) -> List[Dict[str, Any]]:
	feed = feedparser.parse(xml_text)
	results: List[Dict[str, Any]] = []
	for e in feed.entries:
		arxiv_id = _extract_arxiv_id(getattr(e, "id", ""))
		published = getattr(e, "published", None)
		title = getattr(e, "title", "")
		summary = getattr(e, "summary", "")
		authors = [a.name for a in getattr(e, "authors", [])] if hasattr(e, "authors") else []
		categories = [t.term for t in getattr(e, "tags", [])] if hasattr(e, "tags") else []
		links = getattr(e, "links", [])
		pdf_url = None
		for ln in links or []:
			if isinstance(ln, dict):
				if ln.get("type") == "application/pdf":
					pdf_url = ln.get("href")
					break
		results.append(
			{
				"arxiv_id": arxiv_id,
				"entry_id": getattr(e, "id", ""),
				"title": title,
				"summary": summary,
				"authors": authors,
				"categories": categories,
				"published": published,
				"pdf_url": pdf_url,
			}
		)
	return results


async def _fetch_all_for_year(query: str, page_size: int, max_pages: int) -> List[Dict[str, Any]]:
	records: List[Dict[str, Any]] = []
	async with httpx.AsyncClient(headers={"User-Agent": "agents-papers/0.1"}) as client:
		start = 0
		for _ in range(max_pages):
			xml = await _fetch_page(client, query=query, start=start, max_results=page_size)
			if "<entry" not in xml:
				break
			entries = _parse_entries(xml)
			if not entries:
				break
			records.extend(entries)
			start += page_size
			await asyncio.sleep(0.6)
	return records


def fetch_arxiv_surveys_for_year(
	year: int,
	page_size: int = 100,
	max_pages: int = 30,
) -> List[Dict[str, Any]]:
	"""
	Fetch arXiv surveys for a given year and return normalized entries.
	"""
	query = build_survey_query(year=year)
	logger.info("arXiv survey query (year=%s)=%s", year, query)

	async def _run() -> List[Dict[str, Any]]:
		return await _fetch_all_for_year(query=query, page_size=page_size, max_pages=max_pages)

	return asyncio.run(_run())


def write_year_file(base_dir: Path, year: int, items: List[Dict[str, Any]]) -> Path:
	# Deduplicate by arxiv_id within the same year
	seen: set[str] = set()
	deduped: List[Dict[str, Any]] = []
	for it in items:
		aid = it.get("arxiv_id") or ""
		if aid in seen:
			continue
		seen.add(aid)
		deduped.append(it)
	year_dir = base_dir / str(year)
	year_dir.mkdir(parents=True, exist_ok=True)
	out_path = year_dir / f"arxiv-{year}-surveys.json"
	out_path.write_text(__import__("json").dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8")
	return out_path


