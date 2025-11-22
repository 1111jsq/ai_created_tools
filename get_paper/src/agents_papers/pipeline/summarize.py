from __future__ import annotations

from typing import List

from agents_papers.models.paper import Paper


def _truncate(text: str, limit: int = 500) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def summarize_papers(papers: List[Paper]) -> List[Paper]:
    # Placeholder: keep abstract but truncate to a readable length
    for p in papers:
        if p.abstract:
            p.abstract = _truncate(p.abstract, limit=800)
    return papers


