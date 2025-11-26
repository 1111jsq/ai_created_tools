from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from agents_papers.sources.arxiv import fetch_arxiv_raw

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

    return all_records


