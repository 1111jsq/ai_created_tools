from __future__ import annotations

from datetime import datetime
from hashlib import sha1
from typing import List, Optional

from pydantic import BaseModel, Field


def _normalize_string(value: str) -> str:
    return " ".join(value.strip().lower().split())


def generate_stable_paper_id(
    title: str,
    authors: List[str],
    doi: Optional[str] = None,
    arxiv_id: Optional[str] = None,
) -> str:
    if doi:
        return f"doi:{doi.strip().lower()}"
    if arxiv_id:
        return f"arxiv:{arxiv_id.strip().lower()}"
    normalized_title = _normalize_string(title)
    normalized_authors = ",".join(_normalize_string(a) for a in authors)
    digest = sha1(f"{normalized_title}|{normalized_authors}".encode("utf-8")).hexdigest()[:16]
    return f"hash:{digest}"


class Paper(BaseModel):
    paperId: str = Field(..., description="Stable unique identifier for the paper")
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    venue: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    primaryUrl: Optional[str] = None
    pdfUrl: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def from_minimal(
        title: str,
        authors: List[str],
        abstract: str = "",
        venue: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        primaryUrl: Optional[str] = None,
        pdfUrl: Optional[str] = None,
        sources: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        doi: Optional[str] = None,
        arxiv_id: Optional[str] = None,
    ) -> "Paper":
        paper_id = generate_stable_paper_id(title, authors, doi=doi, arxiv_id=arxiv_id)
        return Paper(
            paperId=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            venue=venue,
            year=year,
            month=month,
            primaryUrl=primaryUrl,
            pdfUrl=pdfUrl,
            sources=sources or [],
            topics=topics or [],
            tags=tags or [],
        )


