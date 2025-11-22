from __future__ import annotations

import argparse
import glob
import json
import os
from typing import List, Dict, Any, Optional

DEFAULT_EXPORT_DIR = os.path.join("data", "exports")


def _latest_run_dir(base_dir: str) -> Optional[str]:
    if not os.path.isdir(base_dir):
        return None
    candidates = [d for d in glob.glob(os.path.join(base_dir, "*")) if os.path.isdir(d)]
    if not candidates:
        return None
    candidates.sort(reverse=True)  # names are timestamped, lexical works
    return candidates[0]


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def list_items(run_dir: str, limit: int, contains: Optional[str]) -> None:
    jsonl_path = os.path.join(run_dir, "news.jsonl")
    if not os.path.exists(jsonl_path):
        print(f"未找到文件: {jsonl_path}")
        return
    rows = _load_jsonl(jsonl_path)
    if contains:
        key = contains.lower()
        rows = [r for r in rows if key in (r.get("title") or "").lower()]
    print(f"目录: {run_dir}  共 {len(rows)} 条，显示上限 {limit}")
    print("source | title | url")
    print("-" * 80)
    for r in rows[:limit]:
        source = (r.get("source") or "")[:24]
        title = (r.get("title") or "")[:40]
        url = (r.get("url") or "")[:80]
        print(f"{source} | {title} | {url}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect exported news files")
    parser.add_argument("--export-dir", default=DEFAULT_EXPORT_DIR, help="导出根目录")
    parser.add_argument("--run", default=None, help="指定运行目录名（如 20250101_090000），默认取最新")
    parser.add_argument("--limit", type=int, default=20, help="展示记录上限")
    parser.add_argument("--contains", default=None, help="按标题包含关键字过滤（不区分大小写）")
    args = parser.parse_args()

    base = args.export_dir
    run_dir = os.path.join(base, args.run) if args.run else _latest_run_dir(base)
    if not run_dir:
        print(f"未找到任何运行目录于: {base}")
        return 1
    list_items(run_dir, limit=args.limit, contains=args.contains)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
