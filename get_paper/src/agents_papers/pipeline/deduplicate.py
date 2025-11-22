from __future__ import annotations

from typing import Dict, List

from agents_papers.models.paper import Paper


def deduplicate_papers(papers: List[Paper]) -> List[Paper]:
    seen: Dict[str, Paper] = {}
    for p in papers:
        if p.paperId not in seen:
            seen[p.paperId] = p
    return list(seen.values())


