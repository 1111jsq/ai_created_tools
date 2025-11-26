"""数据读取模块"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import NewsAggItem, PaperItem, ReleaseAggItem
from .utils import parse_iso_flexible, within_range


def read_paper_dir(dir_path: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    """从目录读取论文数据，返回原始字典列表"""
    data: List[Dict[str, Any]] = []
    ranked_all = next(iter(dir_path.glob("*-ranked-all.json")), None)
    if ranked_all and ranked_all.exists():
        try:
            data = json.loads(ranked_all.read_text(encoding="utf-8")) or []
            if not isinstance(data, list):
                data = []
        except Exception as e:
            logger.exception("读取论文 ranked-all 失败: %s", e)
            data = []
    if not data:
        # fallback to <label>-agents-papers.json
        agents_json = next(iter(dir_path.glob("*-agents-papers.json")), None)
        if agents_json and agents_json.exists():
            try:
                j = json.loads(agents_json.read_text(encoding="utf-8")) or []
                if isinstance(j, list):
                    data = j
            except Exception as e:
                logger.exception("读取论文 agents-papers.json 失败: %s", e)
    return data


def read_papers(
    paper_root: Path,
    label: str,
    logger: logging.Logger,
    start_dt: Optional[datetime] = None,
    end_dt: Optional[datetime] = None,
) -> List[PaperItem]:
    """读取论文数据"""
    from .utils import parse_label_to_range
    
    exports_root = paper_root / "exports"
    exports_dir = exports_root / label
    items: List[PaperItem] = []
    
    # helper to convert dict -> PaperItem with date filter
    def _append_from_dicts(dicts: List[Dict[str, Any]]) -> None:
        for d in dicts:
            pub = d.get("submitted_date") or d.get("published_at")
            pub_dt = parse_iso_flexible(pub or "")
            if start_dt and end_dt:
                # 若缺少具体时间戳，仍允许加入（因为当前目录标签已与区间重叠）
                if pub_dt and (not within_range(pub_dt, start_dt, end_dt)):
                    continue
            items.append(
                PaperItem(
                    title=d.get("title") or d.get("normalized_title") or "",
                    authors=d.get("authors") or d.get("normalized_authors"),
                    source=d.get("source") or d.get("origin") or None,
                    published_at=pub,
                    tags=d.get("tags") or d.get("topics"),
                    score=d.get("score"),
                    rank=d.get("rank"),
                )
            )

    if exports_dir.exists():
        try:
            _append_from_dicts(read_paper_dir(exports_dir, logger))
        except Exception as e:
            logger.exception("读取论文目录失败: %s", e)
        return items

    # fallback: scan overlapping labels under exports_root
    if not exports_root.exists():
        logger.info("Paper exports root not found: %s", str(exports_root))
        return items
    logger.info("Paper label dir missing, scan overlaps under: %s", str(exports_root))
    try:
        for sub in sorted([p for p in exports_root.iterdir() if p.is_dir()]):
            rng = parse_label_to_range(sub.name)
            if not rng or not (start_dt and end_dt):
                continue
            s2, e2 = rng
            # overlap if ranges intersect
            if not (e2 < start_dt or s2 > end_dt):
                _append_from_dicts(read_paper_dir(sub, logger))
    except Exception as e:
        logger.exception("扫描论文导出目录失败: %s", e)
    return items


def extract_summaries_from_markdown(content: str, title_to_summary: Dict[str, str]) -> None:
    """从markdown内容中提取标题和摘要"""
    # 支持多种格式：
    # 1. ## 标题 ... ### 摘要 ... 摘要内容
    # 2. ## 标题 ... **摘要** ... 摘要内容
    # 3. ## 标题 ... 摘要: ... 摘要内容
    
    # 模式1：标准的 ## 标题 + ### 摘要
    pattern1 = r'##\s+(.+?)\n.*?###\s+摘要\s*\n\s*\n(.+?)(?=\n---|\n##|$)'
    matches1 = re.finditer(pattern1, content, re.DOTALL)
    for match in matches1:
        title = match.group(1).strip()
        summary = match.group(2).strip()
        if title and summary:
            # 清理摘要文本
            summary = re.sub(r'\s+', ' ', summary).strip()
            # 移除可能的markdown格式标记
            summary = re.sub(r'\*\*', '', summary)
            if summary:
                title_to_summary[title] = summary
    
    # 模式2：## 标题 + **摘要**
    pattern2 = r'##\s+(.+?)\n.*?\*\*摘要\*\*\s*\n\s*\n(.+?)(?=\n---|\n##|$)'
    matches2 = re.finditer(pattern2, content, re.DOTALL)
    for match in matches2:
        title = match.group(1).strip()
        summary = match.group(2).strip()
        if title and summary:
            summary = re.sub(r'\s+', ' ', summary).strip()
            summary = re.sub(r'\*\*', '', summary)
            if summary and title not in title_to_summary:  # 避免覆盖已有的
                title_to_summary[title] = summary
    
    # 模式3：## 标题 + 摘要:
    pattern3 = r'##\s+(.+?)\n.*?摘要[:：]\s*\n\s*\n(.+?)(?=\n---|\n##|$)'
    matches3 = re.finditer(pattern3, content, re.DOTALL)
    for match in matches3:
        title = match.group(1).strip()
        summary = match.group(2).strip()
        if title and summary:
            summary = re.sub(r'\s+', ' ', summary).strip()
            summary = re.sub(r'\*\*', '', summary)
            if summary and title not in title_to_summary:
                title_to_summary[title] = summary


def read_news(
    news_exports_root: Path,
    start_dt: datetime,
    end_dt: datetime,
    logger: logging.Logger,
) -> List[NewsAggItem]:
    """读取资讯数据，并从markdown文件提取摘要"""
    items: List[NewsAggItem] = []
    if not news_exports_root.exists():
        logger.info("News exports root not found: %s", str(news_exports_root))
        return items
    
    # 用于存储标题到摘要的映射
    title_to_summary: Dict[str, str] = {}
    
    # 先读取markdown文件提取摘要
    try:
        for run_dir in sorted(news_exports_root.iterdir()):
            if not run_dir.is_dir():
                continue
            markdown_root = run_dir / "markdown" / "news"
            if markdown_root.exists():
                # 遍历日期目录结构 YYYY/MM/DD/YYYY-MM-DD.md
                for year_dir in markdown_root.iterdir():
                    if not year_dir.is_dir():
                        continue
                    for month_dir in year_dir.iterdir():
                        if not month_dir.is_dir():
                            continue
                        for day_dir in month_dir.iterdir():
                            if not day_dir.is_dir():
                                continue
                            md_file = day_dir / f"{day_dir.name}.md"
                            if md_file.exists():
                                try:
                                    content = md_file.read_text(encoding="utf-8")
                                    # 解析markdown提取标题和摘要
                                    extract_summaries_from_markdown(content, title_to_summary)
                                except Exception as e:
                                    logger.debug("读取markdown文件失败: %s, %s", md_file, e)
    except Exception as e:
        logger.warning("读取markdown摘要失败: %s", e)
    
    # 读取jsonl文件
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
                    pub_dt = parse_iso_flexible(row.get("published_at") or "")
                    fetched_dt = parse_iso_flexible(row.get("fetched_at") or "")
                    basis = pub_dt or fetched_dt
                    if within_range(basis, start_dt, end_dt):
                        title = row.get("title") or ""
                        # 添加摘要信息到tags（临时存储，后续会提取）
                        summary = title_to_summary.get(title, "")
                        tags = row.get("tags") or []
                        if summary:
                            # 将完整摘要作为额外信息存储（不截断，后续在显示时再截断）
                            tags.append(f"摘要: {summary}")
                        
                        items.append(
                            NewsAggItem(
                                title=title,
                                url=row.get("url") or "",
                                published_at=row.get("published_at"),
                                fetched_at=row.get("fetched_at") or "",
                                source=row.get("source") or "",
                                source_type=row.get("source_type") or "",
                                tags=tags,
                                score=None,
                            )
                        )
    except Exception as e:
        logger.exception("Failed reading news: %s", e)
    return items


def read_releases(
    sdk_data_root: Path,
    start_dt: datetime,
    end_dt: datetime,
    repos_filter: Optional[List[str]],
    logger: logging.Logger,
) -> List[ReleaseAggItem]:
    """读取SDK发布数据，并提取变更信息"""
    releases_dir = sdk_data_root / "releases"
    summaries_dir = sdk_data_root / "summaries"
    items: List[ReleaseAggItem] = []
    if not releases_dir.exists():
        logger.info("SDK releases directory not found: %s", str(releases_dir))
        return items
    md_files = list(releases_dir.glob("*.md"))
    repo_pat = re.compile(r"^# Releases Page \d+ - ([\w\-/\.]+)", re.MULTILINE)
    name_pat = re.compile(r"^## \d+\. (.+)$", re.MULTILINE)
    tag_pat = re.compile(r"^- \*\*Tag\*\*: (.+)$", re.MULTILINE)
    url_pat = re.compile(r"^- \*\*URL\*\*: (.+)$", re.MULTILINE)
    pub_pat = re.compile(r"^- \*\*Published At\*\*: (.+)$", re.MULTILINE)
    notes_pat = re.compile(r"^### Notes\s*\n(.*?)(?=\n---|\n## |$)", re.MULTILINE | re.DOTALL)

    def _extract_highlights_from_notes(notes_text: str) -> List[str]:
        """从 Notes 部分提取关键变更信息"""
        if not notes_text:
            return []
        highlights = []
        lines = notes_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # 提取关键变更：feat, fix, chore, style 等开头的行
            if any(line.startswith(prefix) for prefix in ['feat', 'fix', 'chore', 'style', 'refactor', 'perf', 'docs']):
                # 移除前缀，提取描述
                parts = line.split(':', 1)
                if len(parts) > 1:
                    desc = parts[1].strip()
                    if desc and len(desc) < 200:  # 限制长度
                        highlights.append(desc)
                elif len(line) < 200:
                    highlights.append(line)
            # 也提取 release 相关的信息
            elif 'release' in line.lower() and len(line) < 200:
                highlights.append(line)
        return highlights[:5]  # 最多返回5条

    def _load_summary_highlights(repo: str, page: int) -> List[str]:
        """从 summaries 目录加载摘要信息"""
        if not summaries_dir.exists():
            return []
        summary_file = summaries_dir / f"{repo.replace('/', '_')}_{page}_summary.md"
        if not summary_file.exists():
            return []
        try:
            content = summary_file.read_text(encoding="utf-8")
            highlights = []
            # 提取高重要性变更
            high_importance = re.findall(r'## 高重要性[^\n]*\n(.*?)(?=## |$)', content, re.DOTALL)
            for section in high_importance:
                # 提取版本和变更项
                items = re.findall(r'\*\*[^*]+\*\*\s*\n((?:- .+\n?)+)', section)
                for item_group in items:
                    items_list = re.findall(r'- (.+)', item_group)
                    highlights.extend(items_list[:3])  # 每个版本最多3条
            return highlights[:10]  # 最多返回10条
        except Exception:
            return []

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
        
        # 尝试从文件名提取页码
        page_num = 1
        page_match = re.search(r'_(\d+)\.md$', path.name)
        if page_match:
            try:
                page_num = int(page_match.group(1))
            except Exception:
                pass
        
        # 加载摘要信息
        summary_highlights = _load_summary_highlights(repo, page_num)
        
        # Split by sections starting with "## "
        sections = [s.strip() for s in content.split("\n## ") if s.strip()]
        for sec in sections:
            # restore header if split removed it
            sec_txt = "## " + sec if not sec.startswith("## ") else sec
            name_m = name_pat.search(sec_txt)
            tag_m = tag_pat.search(sec_txt)
            url_m = url_pat.search(sec_txt)
            pub_m = pub_pat.search(sec_txt)
            notes_m = notes_pat.search(sec_txt)
            
            published_str = pub_m.group(1).strip() if pub_m else ""
            published_dt = parse_iso_flexible(published_str)
            if not within_range(published_dt, start_dt, end_dt):
                continue
            
            # 提取变更信息
            highlights = []
            if notes_m:
                notes_text = notes_m.group(1).strip()
                highlights = _extract_highlights_from_notes(notes_text)
            
            # 如果没有从 Notes 提取到，使用摘要信息（但要去重）
            if not highlights and summary_highlights:
                # 去重：避免同一仓库的不同版本显示相同的变更信息
                seen_highlights = set()
                for h in summary_highlights[:5]:
                    # 简单去重：如果变更信息太相似，跳过
                    h_clean = h.lower().strip()
                    if h_clean and h_clean not in seen_highlights:
                        seen_highlights.add(h_clean)
                        highlights.append(h)
            
            items.append(
                ReleaseAggItem(
                    repo=repo,
                    tag=(tag_m.group(1).strip() if tag_m else ""),
                    name=(name_m.group(1).strip() if name_m else ""),
                    url=(url_m.group(1).strip() if url_m else ""),
                    published_at=published_dt.isoformat() if published_dt else published_str,
                    highlights=highlights if highlights else None,
                )
            )
    return items

