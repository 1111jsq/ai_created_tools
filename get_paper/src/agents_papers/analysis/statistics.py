from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from agents_papers.models.paper import Paper


@dataclass
class StatsReport:
    total: int
    top_authors: List[Tuple[str, int]]
    top_tags: List[Tuple[str, int]]
    topics_distribution: List[Tuple[str, int]]


@dataclass
class AdvancedStatsReport:
    tag_cooccurrence: List[Tuple[Tuple[str, str], int]]
    topic_tag_association: Dict[str, List[Tuple[str, int]]]
    time_distribution: Dict[str, int]
    source_distribution: List[Tuple[str, int]]
    venue_distribution: List[Tuple[str, int]]


def generate_statistics(papers: Iterable[Paper], top_k: int = 10) -> StatsReport:
    authors_counter: Counter[str] = Counter()
    tags_counter: Counter[str] = Counter()
    topics_counter: Counter[str] = Counter()

    total = 0
    for p in papers:
        total += 1
        authors_counter.update(p.authors)
        tags_counter.update(p.tags)
        topics_counter.update(p.topics)

    return StatsReport(
        total=total,
        top_authors=authors_counter.most_common(top_k),
        top_tags=tags_counter.most_common(top_k),
        topics_distribution=topics_counter.most_common(top_k),
    )


def generate_advanced_statistics(papers: Iterable[Paper], top_k: int = 10) -> AdvancedStatsReport:
    tag_cooccurrence_counter: Counter[Tuple[str, str]] = Counter()
    topic_tag_counter: Dict[str, Counter[str]] = defaultdict(Counter)
    time_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    venue_counter: Counter[str] = Counter()

    for p in papers:
        # 标签共现分析
        tags_list = sorted(p.tags)
        for i, tag1 in enumerate(tags_list):
            for tag2 in tags_list[i + 1:]:
                tag_cooccurrence_counter[(tag1, tag2)] += 1

        # 主题-标签关联
        for topic in p.topics:
            topic_tag_counter[topic].update(p.tags)

        # 时间分布（按年月）
        if p.year and p.month:
            time_key = f"{p.year}-{p.month:02d}"
            time_counter[time_key] += 1
        elif p.year:
            time_key = f"{p.year}"
            time_counter[time_key] += 1

        # 数据源分布
        source_counter.update(p.sources)

        # 会议/期刊分布
        if p.venue:
            venue_counter[p.venue] += 1

    # 构建主题-标签关联字典
    topic_tag_association: Dict[str, List[Tuple[str, int]]] = {}
    for topic, tag_counter in topic_tag_counter.items():
        topic_tag_association[topic] = tag_counter.most_common(top_k)

    return AdvancedStatsReport(
        tag_cooccurrence=tag_cooccurrence_counter.most_common(top_k * 2),
        topic_tag_association=topic_tag_association,
        time_distribution=dict(time_counter),
        source_distribution=source_counter.most_common(top_k),
        venue_distribution=venue_counter.most_common(top_k),
    )


