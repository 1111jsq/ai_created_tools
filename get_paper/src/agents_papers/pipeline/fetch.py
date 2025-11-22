from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import os

from agents_papers.sources.arxiv import fetch_arxiv_raw
from agents_papers.sources.openreview import fetch_openreview_raw
from agents_papers.sources.openreview_v2 import fetch_openreview_v2_raw
from agents_papers.config import OPENREVIEW_CONFIG

logger = logging.getLogger(__name__)


def _write_raw(records: List[Dict[str, Any]], out_dir: Path, source: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, rec in enumerate(records):
        path = out_dir / f"{source}-{i:03d}.json"
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_all_sources(month: str, output_dir: Path, submitted_start: str | None = None, submitted_end: str | None = None) -> List[Dict[str, Any]]:
    all_records: List[Dict[str, Any]] = []
    # arXiv with pagination and institution focus
    institutions = [
        "Google", "DeepMind", "Microsoft", "OpenAI", "Meta", "Apple",
        "Stanford", "MIT", "CMU", "Berkeley", "Oxford", "Harvard",
        "Tsinghua", "Peking University", "PKU", "USTC", "SJTU",
        "Princeton", "UCLA", "UCSD", "ETH Zurich", "NUS", "NTU",
    ]
    arxiv_records = fetch_arxiv_raw(
        month=month,
        limit=250,
        page_size=50,
        max_pages=5,
        institutions=institutions,
        categories=["cs.AI", "cs.LG", "cs.MA"],
        keywords=None,
        submitted_start=submitted_start,
        submitted_end=submitted_end,
    )
    _write_raw(arxiv_records, output_dir / "arxiv", "arxiv")
    all_records.extend(arxiv_records)

    # OpenReview (可配置启用：优先 v2 客户端，失败再回退 v1)
    enabled = (os.getenv("OPENREVIEW_ENABLED", "1" if OPENREVIEW_CONFIG.get("enabled", False) else "0") == "1")
    if enabled:
        # v2 首选：需要 venue_id
        venue_id = OPENREVIEW_CONFIG.get("venue_id") or os.getenv("OPENREVIEW_VENUE_ID", "")
        status = OPENREVIEW_CONFIG.get("status") or os.getenv("OPENREVIEW_STATUS", "all")
        v2_records = fetch_openreview_v2_raw(
            month=month,
            venue_id=venue_id if venue_id else None,
            status=status or "all",
            limit=min(OPENREVIEW_CONFIG.get("page_size", 50) * OPENREVIEW_CONFIG.get("max_pages", 4), 500),
        )
        if v2_records:
            _write_raw(v2_records, output_dir / "openreview", "openreview")
            all_records.extend(v2_records)
        else:
            openreview_records = fetch_openreview_raw(
                month=month,
                limit=min(OPENREVIEW_CONFIG.get("page_size", 50) * OPENREVIEW_CONFIG.get("max_pages", 4), 500),
                page_size=OPENREVIEW_CONFIG.get("page_size", 50),
                max_pages=OPENREVIEW_CONFIG.get("max_pages", 4),
                venues=OPENREVIEW_CONFIG.get("venues") or None,
                query=OPENREVIEW_CONFIG.get("query") or None,
                submitted_start=submitted_start,
                submitted_end=submitted_end,
            )
            _write_raw(openreview_records, output_dir / "openreview", "openreview")
            all_records.extend(openreview_records)

    return all_records


