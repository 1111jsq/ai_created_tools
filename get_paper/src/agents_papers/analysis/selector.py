from __future__ import annotations

from typing import Dict, List, Tuple

from agents_papers.models.paper import Paper


def _compute_composite_score(p: Paper, analysis: Dict[str, object] | None) -> float:
    score = 0.0
    text = f"{p.title} {p.abstract}".lower()
    # Heuristics: venue weight, tag variety, length, llm novelty
    if p.venue and p.venue.lower() in {"arxiv", "neurips", "iclr", "icml", "acl"}:
        score += 1.0
    score += min(len(p.tags), 6) * 0.2
    score += (len(p.title.split()) >= 6) * 0.3
    score += (len(p.abstract.split()) >= 120) * 0.4
    novelty = 0.0
    if analysis and isinstance(analysis.get("novelty_score", 0), (int, float)):
        novelty = float(analysis.get("novelty_score", 0))
    score += novelty * 0.8
    return score


def select_top_k(papers: List[Paper], analyses: List[Dict[str, object]], k: int = 10) -> List[Tuple[Paper, Dict[str, object] | None]]:
    id_to_analysis: Dict[str, Dict[str, object]] = {a.get("paperId"): a.get("analysis") for a in analyses}
    scored = [
        (p, _compute_composite_score(p, id_to_analysis.get(p.paperId))) for p in papers
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [(p, id_to_analysis.get(p.paperId)) for p, _ in scored[:k]]
    return top


def rank_papers(papers: List[Paper], analyses: List[Dict[str, object]]) -> List[Tuple[Paper, Dict[str, object] | None, float]]:
    """Return all papers ranked with attached analysis and score."""
    id_to_analysis: Dict[str, Dict[str, object]] = {a.get("paperId"): a.get("analysis") for a in analyses}
    scored = [
        (p, id_to_analysis.get(p.paperId), _compute_composite_score(p, id_to_analysis.get(p.paperId)))
        for p in papers
    ]
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored


