from __future__ import annotations

import argparse
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ----------------------------
# CLI & Time utils
# ----------------------------

def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _format_yyyymmdd(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def _derive_range(start: Optional[str], end: Optional[str], last_days: Optional[int]) -> Tuple[datetime, datetime]:
    if start and end:
        s = _parse_date(start)
        e = _parse_date(end)
        if e < s:
            raise ValueError("end must be >= start")
        return s, e
    # 默认最近 7 天（含今天）
    days = last_days if (last_days and last_days > 0) else 7
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt = today - timedelta(days=days - 1)
    end_dt = today
    return start_dt, end_dt


def _derive_label(start_dt: datetime, end_dt: datetime) -> str:
    return f"{_format_yyyymmdd(start_dt)}-{_format_yyyymmdd(end_dt)}"


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


# ----------------------------
# Data models
# ----------------------------

@dataclass
class PaperItem:
    title: str
    authors: List[str] | str | None = None
    source: str | None = None
    published_at: Optional[str] = None
    tags: List[str] | None = None
    score: Optional[float] = None
    rank: Optional[int] = None


@dataclass
class NewsAggItem:
    title: str
    url: str
    published_at: Optional[str]
    fetched_at: str
    source: str
    source_type: str
    tags: List[str] | None = None
    score: Optional[float] = None


@dataclass
class ReleaseAggItem:
    repo: str
    tag: str
    name: str
    url: str
    published_at: str
    highlights: Optional[List[str]] = None


# ----------------------------
# Helpers
# ----------------------------

def _parse_iso_flexible(s: str) -> Optional[datetime]:
    if not s:
        return None
    # Try common formats
    candidates = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    # Handle 'Z' timezone
    ss = s.strip().replace("Z", "+0000").replace("+00:00", "+0000")
    for fmt in candidates:
        try:
            if "%z" in fmt:
                return datetime.strptime(ss, fmt)
            else:
                return datetime.strptime(ss, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def _within_range(dt: Optional[datetime], start_dt: datetime, end_dt: datetime) -> bool:
    if not dt:
        return False
    return start_dt <= dt.replace(tzinfo=timezone.utc) <= end_dt


def _sanitize_mermaid_text(text: str) -> str:
    # Remove parentheses/brackets/braces from labels due to rendering constraints
    return re.sub(r"[()\\[\\]{}]", "", text or "")


# ----------------------------
# Readers
# ----------------------------

def read_papers(paper_root: Path, label: str, logger: logging.Logger) -> List[PaperItem]:
    """Read papers from get_paper/data/exports/<label> if present."""
    exports_dir = paper_root / "exports" / label
    items: List[PaperItem] = []
    if not exports_dir.exists():
        logger.warning("Paper exports directory not found: %s", str(exports_dir))
        return items

    ranked_all = exports_dir / f"{label}-ranked-all.json"
    stats_json = exports_dir / f"{label}-stats.json"
    try:
        if ranked_all.exists():
            data = json.loads(ranked_all.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for d in data:
                    items.append(
                        PaperItem(
                            title=d.get("title") or d.get("normalized_title") or "",
                            authors=d.get("authors") or d.get("normalized_authors"),
                            source=d.get("source") or d.get("origin") or None,
                            published_at=d.get("submitted_date") or d.get("published_at"),
                            tags=d.get("tags"),
                            score=d.get("score"),
                            rank=d.get("rank"),
                        )
                    )
        elif stats_json.exists():
            # Fallback: only counts available; keep empty items list but allow stats usage later
            logger.info("Paper ranked-all missing; will rely on stats.json for counts: %s", str(stats_json))
        else:
            logger.warning("No recognizable paper outputs under: %s", str(exports_dir))
    except Exception as e:
        logger.exception("Failed reading papers: %s", e)
    return items


def read_news(news_exports_root: Path, start_dt: datetime, end_dt: datetime, logger: logging.Logger) -> List[NewsAggItem]:
    """Scan get_agent_news/data/exports/<run_dir>/news.jsonl and filter by range."""
    items: List[NewsAggItem] = []
    if not news_exports_root.exists():
        logger.warning("News exports root not found: %s", str(news_exports_root))
        return items
    try:
        for run_dir in sorted(news_exports_root.iterdir()):
            if not run_dir.is_dir():
                continue
            jsonl = run_dir / "news.jsonl"
            if not jsonl.exists():
                continue
            with jsonl.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    pub_dt = _parse_iso_flexible(row.get("published_at") or "")
                    fetched_dt = _parse_iso_flexible(row.get("fetched_at") or "")
                    basis = pub_dt or fetched_dt
                    if _within_range(basis, start_dt, end_dt):
                        items.append(
                            NewsAggItem(
                                title=row.get("title") or "",
                                url=row.get("url") or "",
                                published_at=row.get("published_at"),
                                fetched_at=row.get("fetched_at") or "",
                                source=row.get("source") or "",
                                source_type=row.get("source_type") or "",
                                tags=row.get("tags") or [],
                                score=row.get("score"),
                            )
                        )
    except Exception as e:
        logger.exception("Failed reading news: %s", e)
    return items


def read_releases(sdk_data_root: Path, start_dt: datetime, end_dt: datetime, repos_filter: Optional[List[str]], logger: logging.Logger) -> List[ReleaseAggItem]:
    """Read markdown pages under data/releases and filter by Published At."""
    releases_dir = sdk_data_root / "releases"
    items: List[ReleaseAggItem] = []
    if not releases_dir.exists():
        logger.warning("SDK releases directory not found: %s", str(releases_dir))
        return items
    md_files = list(releases_dir.glob("*.md"))
    repo_pat = re.compile(r"^# Releases Page \d+ - ([\w\-/\.]+)", re.MULTILINE)
    name_pat = re.compile(r"^## \d+\. (.+)$", re.MULTILINE)
    tag_pat = re.compile(r"^- \*\*Tag\*\*: (.+)$", re.MULTILINE)
    url_pat = re.compile(r"^- \*\*URL\*\*: (.+)$", re.MULTILINE)
    pub_pat = re.compile(r"^- \*\*Published At\*\*: (.+)$", re.MULTILINE)

    for path in md_files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        repo_match = repo_pat.search(content)
        repo = repo_match.group(1) if repo_match else ""
        if repos_filter and repo not in set(repos_filter):
            # skip pages not in filter
            continue
        # Split by sections starting with "## "
        sections = [s.strip() for s in content.split("\n## ") if s.strip()]
        for sec in sections:
            # restore header if split removed it
            sec_txt = "## " + sec if not sec.startswith("## ") else sec
            name_m = name_pat.search(sec_txt)
            tag_m = tag_pat.search(sec_txt)
            url_m = url_pat.search(sec_txt)
            pub_m = pub_pat.search(sec_txt)
            published_str = pub_m.group(1).strip() if pub_m else ""
            published_dt = _parse_iso_flexible(published_str)
            if not _within_range(published_dt, start_dt, end_dt):
                continue
            items.append(
                ReleaseAggItem(
                    repo=repo,
                    tag=(tag_m.group(1).strip() if tag_m else ""),
                    name=(name_m.group(1).strip() if name_m else ""),
                    url=(url_m.group(1).strip() if url_m else ""),
                    published_at=published_dt.isoformat() if published_dt else published_str,
                    highlights=None,
                )
            )
    return items


# ----------------------------
# Stats & Visualization
# ----------------------------

def _date_range_inclusive(start_dt: datetime, end_dt: datetime) -> List[datetime]:
    days = int((end_dt - start_dt).days)
    return [start_dt + timedelta(days=i) for i in range(days + 1)]


def aggregate_daily_counts(papers: List[PaperItem], news: List[NewsAggItem], releases: List[ReleaseAggItem], start_dt: datetime, end_dt: datetime) -> Dict[str, Dict[str, int]]:
    days = _date_range_inclusive(start_dt, end_dt)
    fmt = "%Y-%m-%d"
    res: Dict[str, Dict[str, int]] = {
        "papers": {d.strftime(fmt): 0 for d in days},
        "news": {d.strftime(fmt): 0 for d in days},
        "sdk": {d.strftime(fmt): 0 for d in days},
    }
    for p in papers:
        dt = _parse_iso_flexible(p.published_at or "")
        if not dt:
            continue
        key = dt.astimezone(timezone.utc).strftime(fmt)
        if key in res["papers"]:
            res["papers"][key] += 1
    for n in news:
        dt = _parse_iso_flexible(n.published_at or n.fetched_at or "")
        if not dt:
            continue
        key = dt.astimezone(timezone.utc).strftime(fmt)
        if key in res["news"]:
            res["news"][key] += 1
    for r in releases:
        dt = _parse_iso_flexible(r.published_at or "")
        if not dt:
            continue
        key = dt.astimezone(timezone.utc).strftime(fmt)
        if key in res["sdk"]:
            res["sdk"][key] += 1
    return res


def build_mermaid_pie(papers_cnt: int, news_cnt: int, sdk_cnt: int) -> str:
    return "\n".join([
        "```mermaid",
        "pie title Source Share",
        f'  "{_sanitize_mermaid_text("Papers")}" : {papers_cnt}',
        f'  "{_sanitize_mermaid_text("News")}" : {news_cnt}',
        f'  "{_sanitize_mermaid_text("SDK Releases")}" : {sdk_cnt}',
        "```",
    ])


def build_mermaid_flow() -> str:
    return "\n".join([
        "```mermaid",
        "flowchart LR",
        f'  A[{_sanitize_mermaid_text("Read Papers")}] --> B[{_sanitize_mermaid_text("Read News")}]',
        f'  B --> C[{_sanitize_mermaid_text("Read SDK Releases")}]',
        f'  C --> D[{_sanitize_mermaid_text("Aggregate Stats")}]',
        f'  D --> E[{_sanitize_mermaid_text("Generate Insights")}]',
        f'  E --> F[{_sanitize_mermaid_text("Write Report")}]',
        "```",
    ])


# ----------------------------
# Insights (LLM optional)
# ----------------------------

def generate_insights(papers: List[PaperItem], news: List[NewsAggItem], releases: List[ReleaseAggItem]) -> str:
    """Template-based insights when LLM not available."""
    lines: List[str] = []
    lines.append("- 本期论文、资讯与 SDK 更新数量已在概览展示。")
    if papers:
        lines.append(f"- 论文样本数 {len(papers)}，建议关注排名靠前与机构背景的论文。")
    else:
        lines.append("- 论文数据缺失，综合判断可能受抓取/时间窗口影响。")
    if news:
        lines.append(f"- 资讯样本数 {len(news)}，建议筛选来源可靠、标签匹配度高的条目。")
    else:
        lines.append("- 资讯数据缺失，建议检查来源配置或抓取窗口。")
    if releases:
        repos = {}
        for r in releases:
            repos[r.repo] = repos.get(r.repo, 0) + 1
        top_repos = sorted(repos.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_repos:
            lines.append("- SDK 活跃仓库 Top: " + ", ".join([f"{k}:{v}" for k, v in top_repos]))
    else:
        lines.append("- SDK 更新数据缺失，可能是时间窗口或限额导致。")
    lines.append("- 若启用 LLM，可生成更深入的趋势洞察与建议。")
    return "\n".join(lines)


def generate_insights_llm(papers: List[PaperItem], news: List[NewsAggItem], releases: List[ReleaseAggItem], logger: logging.Logger) -> str:
    """Attempt LLM call when DEEPSEEK_API_KEY provided; fallback to template."""
    api_key = os.environ.get("DEEPSEEK_API_KEY") or ""
    if not api_key:
        return generate_insights(papers, news, releases)
    try:
        # Minimal REST call to DeepSeek Chat API (hypothetical endpoint)
        import requests  # noqa: WPS433 (stdlib or available in repo)
        prompt = _build_llm_prompt(papers, news, releases)
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是资深技术分析员，请用中文输出深度洞察。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # The actual endpoint may differ; handle failures gracefully.
        resp = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # Common shape: choices[0].message.content
            content = (((data or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            if content.strip():
                logger.info("LLM 分析已启用并成功返回。")
                return content.strip()
        logger.warning("LLM 调用未成功，使用模板化洞察。code=%s", resp.status_code)
        return generate_insights(papers, news, releases)
    except Exception as e:
        logger.exception("LLM 调用失败，使用模板化洞察: %s", e)
        return generate_insights(papers, news, releases)


def _build_llm_prompt(papers: List[PaperItem], news: List[NewsAggItem], releases: List[ReleaseAggItem]) -> str:
    def _clip(txt: str, n: int = 200) -> str:
        return (txt or "")[:n]
    # Limit items to keep prompt small
    p_lines = [f"- { _clip(p.title) }" for p in papers[:50]]
    n_lines = [f"- { _clip(n.title) } ({_clip(n.source)} {_clip(','.join(n.tags or []))})" for n in news[:50]]
    r_lines = [f"- { _clip(r.repo) } { _clip(r.tag) } { _clip(r.name) }" for r in releases[:50]]
    parts = [
        "请基于以下样本生成本期的趋势洞察、主题聚类、重要变更影响与对团队的建议，要求：",
        "1) 全中文；2) 分点列出；3) 不输出任何 Mermaid 文本；4) 若数据源缺失需声明局限。",
        "",
        "【论文样本】",
        *p_lines,
        "",
        "【资讯样本】",
        *n_lines,
        "",
        "【SDK Releases 样本】",
        *r_lines,
    ]
    return "\n".join(parts)


# ----------------------------
# Markdown Report
# ----------------------------

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_report(
    path: Path,
    label: str,
    start_dt: datetime,
    end_dt: datetime,
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
    daily_counts: Dict[str, Dict[str, int]],
    use_llm: bool,
    logger: logging.Logger,
) -> None:
    total_papers = len(papers)
    total_news = len(news)
    total_sdk = len(releases)
    insights = generate_insights_llm(papers, news, releases, logger) if use_llm else generate_insights(papers, news, releases)
    lines: List[str] = []
    lines.append(f"# 智能体每周/区间报告（{label}）")
    lines.append("")
    lines.append("## 概览")
    lines.append(f"- 时间范围: {start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}")
    lines.append(f"- 论文: {total_papers}  条")
    lines.append(f"- 资讯: {total_news}  条")
    lines.append(f"- SDK 更新: {total_sdk}  条")
    lines.append("")
    lines.append("### 来源占比")
    lines.append(build_mermaid_pie(total_papers, total_news, total_sdk))
    lines.append("")
    lines.append("### 编排流程（示意）")
    lines.append(build_mermaid_flow())
    lines.append("")

    # Papers
    lines.append("## 论文")
    if papers:
        for p in papers[:20]:
            lines.append(f"- {p.title}")
    else:
        lines.append("- 数据缺失或不在时间范围内。")
    lines.append("")

    # News
    lines.append("## 资讯")
    if news:
        for n in news[:20]:
            lines.append(f"- {n.title} [{n.source}]")
    else:
        lines.append("- 数据缺失或不在时间范围内。")
    lines.append("")

    # SDK
    lines.append("## SDK 更新")
    if releases:
        for r in releases[:20]:
            lines.append(f"- {r.repo} {r.tag} {r.name} -> {r.url}")
    else:
        lines.append("- 数据缺失或不在时间范围内。")
    lines.append("")

    # Insights
    lines.append("## 综合洞察")
    lines.append(insights)
    lines.append("")

    # Appendix
    lines.append("## 附录")
    lines.append("- 本报告基于已有导出产物聚合生成；若部分数据源缺失，已在上文标注。")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("报告已生成: %s", str(path))


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly/Range Intelligence Report Orchestrator")
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--last-days", type=int, default=7, help="Use last N days when start/end not provided")
    parser.add_argument("--paper-root", default=str(Path("get_paper") / "data"), help="get_paper data root")
    parser.add_argument("--news-root", default=str(Path("get_agent_news") / "data" / "exports"), help="get_agent_news exports root")
    parser.add_argument("--sdk-root", default=str(Path("get_sdk_release_change_log") / "data"), help="sdk release change log data root")
    parser.add_argument("--repos", default="", help="Comma separated repo list filter for SDK, e.g. org1/repo1,org2/repo2")
    parser.add_argument("--output-root", default="reports", help="Output root directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing report if present")
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"), help="Log level")
    args = parser.parse_args()

    _setup_logging(args.log_level)
    logger = logging.getLogger("weekly_report")
    try:
        start_dt, end_dt = _derive_range(args.start, args.end, args.last_days)
        label = _derive_label(start_dt, end_dt)

        paper_root = Path(args.paper_root)
        news_root = Path(args.news_root)
        sdk_root = Path(args.sdk_root)
        output_root = Path(args.output_root)
        out_dir = output_root / label
        _ensure_dir(out_dir)
        out_path = out_dir / "weekly-intel-report.md"
        if out_path.exists() and out_path.stat().st_size > 0 and not args.overwrite:
            logger.info("报告已存在且非空，跳过写入（使用 --overwrite 可覆盖）：%s", str(out_path))
            return 0

        # Read sources
        papers = read_papers(paper_root, label, logger)
        news = read_news(news_root, start_dt, end_dt, logger)
        repos_filter = [s.strip() for s in args.repos.split(",") if s.strip()] if args.repos else None
        releases = read_releases(sdk_root, start_dt, end_dt, repos_filter, logger)

        daily_counts = aggregate_daily_counts(papers, news, releases, start_dt, end_dt)

        use_llm = bool(os.environ.get("DEEPSEEK_API_KEY"))
        write_report(
            path=out_path,
            label=label,
            start_dt=start_dt,
            end_dt=end_dt,
            papers=papers,
            news=news,
            releases=releases,
            daily_counts=daily_counts,
            use_llm=use_llm,
            logger=logger,
        )
        return 0
    except Exception as exc:
        logger.exception("生成报告失败: %s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


