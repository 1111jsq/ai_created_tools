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
        elif source == "openreview":
            payload = rec.get("payload") or {}
            notes = payload.get("notes") or payload.get("items") or []
            if not isinstance(notes, list):
                logger.warning("OpenReview payload notes 非列表，跳过")
                continue
            for note in notes:
                # 兼容结构：字段可能在顶层或 content 中
                content = note.get("content") if isinstance(note, dict) else {}
                # v2 可能为 {"value": ...} 形式
                def _val(x):
                    if isinstance(x, dict):
                        return x.get("value")
                    return x
                raw_title = note.get("title") or (content or {}).get("title") or ""
                title_val = _val(raw_title) or ""
                title = (title_val if isinstance(title_val, str) else str(title_val)).strip()
                # authors 可能是字符串列表、对象列表或单字符串
                raw_authors = note.get("authors") or (content or {}).get("authors") or []
                raw_authors = _val(raw_authors) if raw_authors else raw_authors
                authors: List[str] = []
                if isinstance(raw_authors, list):
                    for a in raw_authors:
                        if isinstance(a, str):
                            if a.strip():
                                authors.append(a.strip())
                        elif isinstance(a, dict):
                            name = a.get("name") or a.get("username") or ""
                            if isinstance(name, str) and name.strip():
                                authors.append(name.strip())
                elif isinstance(raw_authors, str):
                    authors = [s.strip() for s in raw_authors.split(",") if s.strip()]

                raw_abs = note.get("abstract") or (content or {}).get("abstract") or ""
                abs_val = _val(raw_abs) or ""
                abstract = (abs_val if isinstance(abs_val, str) else str(abs_val)).strip()
                note_id = note.get("id") or note.get("_id") or ""
                forum_id = note.get("forum") or note_id
                primary_url = f"https://openreview.net/forum?id={forum_id}" if forum_id else None
                pdf_url = f"https://openreview.net/pdf?id={note_id}" if note_id else None
                venue = note.get("venue") or note.get("venueid") or note.get("invitation")

                # 时间：尝试使用 cdate (ms) 或 mdate/edate；回退 None
                published = None
                for k in ("cdate", "mdate", "edate", "tmdate", "tcdate"):
                    v = note.get(k)
                    if isinstance(v, (int, float)) and v > 0:
                        try:
                            dt = datetime.utcfromtimestamp(int(v) / 1000.0).replace(tzinfo=timezone.utc)
                            published = dt.isoformat()
                            break
                        except Exception:
                            pass

                parsed.append(
                    {
                        "source": "openreview",
                        "title": title,
                        "authors": authors,
                        "abstract": abstract,
                        "primaryUrl": primary_url,
                        "pdfUrl": pdf_url,
                        "venue": venue,
                        "openreview_id": note_id,
                        "published": published,
                        "raw": note,  # 保留一份以便后续需要
                    }
                )
        else:
            logger.warning("Unknown source: %s", source)
    return parsed


