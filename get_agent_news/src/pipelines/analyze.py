from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any

from src.models import NewsItem


def analyze_items(items: List[NewsItem]) -> Dict[str, Any]:
    by_source = Counter([i.source for i in items])
    top_sources = by_source.most_common()
    with_scores = [i for i in items if i.score is not None]
    avg_score = sum(i.score for i in with_scores) / len(with_scores) if with_scores else None
    top5 = [
        {
            "rank": idx + 1,
            "source": i.source,
            "title": i.title,
            "url": i.url,
            "score": i.score,
        }
        for idx, i in enumerate(sorted(items, key=lambda x: (x.score or 0.0), reverse=True)[:5])
    ]
    return {
        "total": len(items),
        "sources": dict(by_source),
        "top_sources": top_sources,
        "avg_score": avg_score,
        "top5": top5,
        "generated_at": datetime.now().isoformat(),
    }


def write_analysis_files(analysis: Dict[str, Any], export_dir: str, items: List[NewsItem]) -> None:
    json_path = f"{export_dir}/analysis.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    md_path = f"{export_dir}/TOP.md"
    lines = ["# 本次抓取 Top 推荐\n"]
    for t in analysis.get("top5", []):
        lines.append(f"- [{t['title']}]({t['url']}) — {t['source']}（score: {t['score']:.2f}）")
    lines.append("\n## 来源分布\n")
    for src, cnt in analysis.get("top_sources", []):
        lines.append(f"- {src}: {cnt}")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
