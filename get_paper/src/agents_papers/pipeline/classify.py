from __future__ import annotations

from typing import List

from agents_papers.models.paper import Paper


KEYWORDS_TO_TAG = {
    "tool use": "tool-use",
    "tool-augmented": "tool-use",
    "toolformer": "tool-use",
    "planning": "planning",
    "planner": "planning",
    "multi-agent": "multi-agent",
    "self-play": "multi-agent",
    "memory": "memory",
    "retrieval": "retrieval",
    "reflection": "reflection",
    "workflow": "workflow",
    "autonomous": "autonomy",
    "agent": "agent",
    "benchmark": "benchmark",
    "evaluation": "evaluation",
    "reasoning": "reasoning",
    "tool": "tool-use",
}


def classify_papers(papers: List[Paper]) -> List[Paper]:
    for p in papers:
        text = f"{p.title} {p.abstract}".lower()
        tags = set(p.tags)
        for kw, tag in KEYWORDS_TO_TAG.items():
            if kw in text:
                tags.add(tag)
        p.tags = sorted(tags)
    return papers


