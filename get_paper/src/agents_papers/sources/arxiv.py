from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


ARXIV_API = "https://export.arxiv.org/api/query"


def _quote(term: str) -> str:
    term = term.strip()
    if " " in term and not (term.startswith('"') and term.endswith('"')):
        return f'"{term}"'
    return term


def build_query(
    keywords: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    institutions: Optional[List[str]] = None,
    submitted_start: Optional[str] = None,
    submitted_end: Optional[str] = None,
) -> str:
    # Build keyword clause on title and abstract
    keys = keywords or [
        "agent",
        "tool use",
        "tool-augmented",
        "planning",
        "multi-agent",
        "autonomous",
        "toolformer",
        "tool learning",
    ]
    keys = [_quote(k) for k in keys]
    ka = [f"ti:{k}" for k in keys] + [f"abs:{k}" for k in keys]
    keyword_clause = " OR ".join(ka)

    # Category filters (arXiv cats)
    cats = categories or ["cs.AI", "cs.LG", "cs.MA"]
    cat_clause = " OR ".join([f"cat:{c}" for c in cats])

    # Institutions focus (approximate via title/abstract match)
    inst_clause = None
    if institutions:
        inst_terms = [_quote(t) for t in institutions]
        inst_fields = [f"ti:{t}" for t in inst_terms] + [f"abs:{t}" for t in inst_terms]
        inst_clause = " OR ".join(inst_fields)

    parts = [f"({keyword_clause})", f"({cat_clause})"]
    if inst_clause:
        parts.append(f"({inst_clause})")
    if submitted_start and submitted_end:
        parts.append(f"submittedDate:[{submitted_start} TO {submitted_end}]")
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


def fetch_arxiv_raw(
    month: str,
    limit: int = 250,
    page_size: int = 50,
    max_pages: int = 5,
    institutions: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    submitted_start: Optional[str] = None,
    submitted_end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    # Returns list of page payloads: {source, fetched_at, payload}
    query = build_query(
        keywords=keywords,
        categories=categories,
        institutions=institutions,
        submitted_start=submitted_start,
        submitted_end=submitted_end,
    )
    logger.info("arXiv query=%s", query)

    async def _run() -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(headers={"User-Agent": "agents-papers/0.1"}) as client:
            start = 0
            fetched = 0
            for _ in range(max_pages):
                xml = await _fetch_page(client, query=query, start=start, max_results=page_size)
                if "<entry" not in xml:
                    break
                records.append(
                    {
                        "source": "arxiv",
                        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
                        "payload": xml,
                    }
                )
                fetched += page_size
                if fetched >= limit:
                    break
                start += page_size
                await asyncio.sleep(0.6)  # QPS <= ~1.6
        return records

    return asyncio.run(_run())


