from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List
from datetime import datetime, timezone

import feedparser

logger = logging.getLogger(__name__)


def parse_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    parsed: List[Dict[str, Any]] = []
    for rec in records:
        source = rec.get("source")
        if source == "arxiv":
            xml = rec["payload"]
            feed = feedparser.parse(xml)
            for entry in feed.get("entries", []):
                authors = [a.get("name", "").strip() for a in entry.get("authors", [])]
                pdf_url = None
                for link in entry.get("links", []):
                    if link.get("type") == "application/pdf":
                        pdf_url = link.get("href")
                        break
                categories = []
                for t in entry.get("tags", []) or []:
                    term = t.get("term")
                    if term:
                        categories.append(term)
                parsed.append(
                    {
                        "source": "arxiv",
                        "title": entry.get("title", "").strip(),
                        "authors": [a for a in authors if a],
                        "abstract": entry.get("summary", "").strip(),
                        "primaryUrl": entry.get("link"),
                        "pdfUrl": pdf_url,
                        "arxiv_id": entry.get("id", "").split("/abs/")[-1],
                        "published": entry.get("published"),
                        "categories": categories,
                    }
                )
        else:
            logger.warning("Unknown source: %s", source)
    return parsed


