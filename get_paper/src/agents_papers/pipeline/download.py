from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import httpx

from agents_papers.models import Paper


logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in name)
    return safe.strip("._") or "file"


def _normalize_pdf_url(raw_url: Optional[str]) -> Optional[str]:
    if not raw_url:
        return None
    url = raw_url.strip()
    # Force https
    if url.startswith("http://"):
        url = "https://" + url[len("http://") :]
    # Ensure arXiv PDF ends with .pdf
    if "arxiv.org/pdf/" in url and not url.lower().endswith(".pdf"):
        url = url + ".pdf"
    return url


async def _download_one(
    client: httpx.AsyncClient,
    paper: Paper,
    target_path: Path,
    timeout: float,
) -> Tuple[str, str | None]:
    paper_id = paper.paperId
    url = _normalize_pdf_url(paper.pdfUrl)
    if not url:
        return paper_id, None
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Skip existing non-empty file
    if target_path.exists() and target_path.stat().st_size > 0:
        return paper_id, str(target_path)

    # Retry with backoff
    attempts = 3
    backoff_base = 0.8
    last_exc: Exception | None = None
    temp_path = target_path.with_suffix(target_path.suffix + ".part")
    for attempt in range(1, attempts + 1):
        try:
            async with client.stream("GET", url, timeout=timeout, follow_redirects=True) as resp:
                resp.raise_for_status()
                # Optionally check content type
                ctype = resp.headers.get("content-type", "").lower()
                # Write to temp then rename
                with temp_path.open("wb") as f:
                    async for chunk in resp.aiter_bytes():
                        if chunk:
                            f.write(chunk)
                temp_path.replace(target_path)
                # Heuristic: consider small files as failure
                if target_path.stat().st_size < 1024:  # <1KB unlikely to be a real PDF
                    raise RuntimeError(f"suspicious small file for {paper_id}")
                # Warn but do not fail if content-type is not clearly PDF
                if "pdf" not in ctype:
                    logger.info("Downloaded %s but content-type=%s", paper_id, ctype or "unknown")
                return paper_id, str(target_path)
        except Exception as exc:
            last_exc = exc
            if attempt < attempts:
                delay = backoff_base * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
            else:
                logger.warning("Failed to download PDF for %s from %s after %d attempts: %s", paper_id, url, attempts, exc)
    # Clean temp file if any
    try:
        if temp_path.exists():
            temp_path.unlink()
    except Exception:
        pass
    return paper_id, None


def _derive_filename(paper: Paper) -> str:
    base = paper.paperId.replace(":", "_")
    base = _sanitize_filename(base)
    if not base.lower().endswith(".pdf"):
        base = f"{base}.pdf"
    return base


def download_pdfs(
    papers: List[Paper],
    pdf_root_dir: Path,
    concurrency: int = 3,
    timeout: int = 60,
) -> Dict[str, str]:
    """
    Download PDFs for provided papers into pdf_root_dir/<source>/ and return a mapping of paperId -> local path.

    - Skips when pdfUrl is missing
    - Skips existing files
    - Writes a manifest.json under pdf_root_dir
    """
    pdf_root_dir.mkdir(parents=True, exist_ok=True)

    async def _run() -> Dict[str, str]:
        sem = asyncio.Semaphore(max(1, concurrency))
        results: Dict[str, str] = {}

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "agents-papers/0.1 (+https://example.local; contact=maintainer)",
                "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
                "Referer": "https://arxiv.org/",
            }
        ) as client:
            tasks = []
            for p in papers:
                if not p.pdfUrl:
                    continue
                first_source = (p.sources[0] if p.sources else "unknown").lower()
                target_dir = pdf_root_dir / first_source
                filename = _derive_filename(p)
                target_path = target_dir / filename

                async def _bounded_download(pp: Paper = p, tp: Path = target_path):
                    async with sem:
                        pid, path_str = await _download_one(client, pp, tp, timeout=timeout)
                        if path_str:
                            results[pid] = path_str

                tasks.append(asyncio.create_task(_bounded_download()))

            if tasks:
                await asyncio.gather(*tasks)

        return results

    mapping = asyncio.run(_run())

    # Persist manifest
    manifest_path = pdf_root_dir / "manifest.json"
    try:
        manifest_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to write PDF manifest: %s", exc)

    logger.info("Downloaded %d PDFs into %s", len(mapping), str(pdf_root_dir))
    return mapping


