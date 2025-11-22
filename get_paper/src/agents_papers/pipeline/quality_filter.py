from __future__ import annotations

import logging
from typing import List

from agents_papers.models.paper import Paper

logger = logging.getLogger(__name__)


INSTITUTION_KEYWORDS = [
    "google", "deepmind", "microsoft", "openai", "meta", "apple",
    "stanford", "mit", "cmu", "berkeley", "oxford", "harvard",
    "tsinghua", "peking university", "pku", "ustc", "sjtu",
    "princeton", "ucla", "ucsd", "eth zurich", "nus", "ntu",
]


POSITIVE_TERMS = [
    "experiment", "experiments", "benchmark", "evaluation", "results",
    "dataset", "code", "open-source", "implementation", "ablation",
]


NEGATIVE_TERMS = [
    "survey", "review", "tutorial", "position paper", "workshop summary",
]


def _score_paper(p: Paper) -> int:
    text = f"{p.title} {p.abstract}".lower()
    score = 0
    if any(inst in text for inst in INSTITUTION_KEYWORDS):
        score += 2
    if len(p.title.split()) >= 6:
        score += 1
    if len(p.abstract.split()) >= 120:  # ~> 800-1000 chars
        score += 1
    if any(term in text for term in POSITIVE_TERMS):
        score += 1
    if any(term in text for term in NEGATIVE_TERMS):
        score -= 1
    return score


def filter_high_quality(papers: List[Paper], min_score: int = 2, require_institution: bool = True) -> List[Paper]:
    filtered: List[Paper] = []
    for p in papers:
        text = f"{p.title} {p.abstract}".lower()
        has_institution = any(inst in text for inst in INSTITUTION_KEYWORDS)
        score = _score_paper(p)
        if require_institution and not has_institution:
            continue
        if score >= min_score:
            filtered.append(p)
    logger.info("Quality filter kept %d / %d papers", len(filtered), len(papers))
    return filtered


