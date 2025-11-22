from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional

import httpx

from agents_papers.config import OPENREVIEW_CONFIG

logger = logging.getLogger(__name__)


def _build_params(
    page_size: int,
    offset: int,
    query: Optional[str],
    venues: Optional[List[str]],
) -> Dict[str, Any]:
    # 为避免强绑定具体 API 形态，这里以最小参数集构造；服务端若忽略未知参数也不影响
    params: Dict[str, Any] = {
        "limit": page_size,
        "offset": offset,
    }
    if query:
        params["query"] = query
    if venues:
        params["venues"] = ",".join(venues)
    return params


def fetch_openreview_raw(
    month: str,
    limit: int = 200,
    page_size: int = 50,
    max_pages: int = 4,
    venues: Optional[List[str]] = None,
    query: Optional[str] = None,
    submitted_start: Optional[str] = None,
    submitted_end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    最小实现：在配置未启用时直接返回空列表；启用后尝试分页获取公开列表。
    注意：OpenReview API 版本较多，参数可能随服务端演进变化；此实现尽量宽容。
    """
    enabled_flag = (os.getenv("OPENREVIEW_ENABLED", "1") == "1") or OPENREVIEW_CONFIG.get("enabled", False)
    if not enabled_flag:
        logger.info("OpenReview 抓取未启用（设置 OPENREVIEW_ENABLED=1 或在配置中开启）")
        return []

    base_url = OPENREVIEW_CONFIG.get("base_url", "https://api.openreview.net").rstrip("/")
    timeout = OPENREVIEW_CONFIG.get("timeout", 30)

    # 选择一个相对稳定的公共列表端点；若后端忽略未知参数则不影响
    notes_url = f"{base_url}/notes"

    records: List[Dict[str, Any]] = []
    fetched = 0
    offset = 0
    page = 0

    with httpx.Client(timeout=timeout, headers={"User-Agent": "agents-papers/0.1"}) as client:
        while page < max_pages and fetched < limit:
            params = _build_params(page_size=page_size, offset=offset, query=query, venues=venues or None)
            payload = None
            try:
                resp = client.get(notes_url, params=params)
                resp.raise_for_status()
                payload = resp.json()
            except httpx.HTTPStatusError as he:
                if he.response is not None and he.response.status_code == 400:
                    safe_params = {"limit": page_size, "offset": offset}
                    logger.info("OpenReview 返回 400，回退为安全参数请求: %s", safe_params)
                    try:
                        resp = client.get(notes_url, params=safe_params)
                        resp.raise_for_status()
                        payload = resp.json()
                    except Exception as e2:
                        # 进一步回退：若提供 venues，尝试常见 invitation 模式
                        fallback_payload = None
                        venue_list = (venues or OPENREVIEW_CONFIG.get("venues") or [])
                        invitation_suffixes = ["/-/Blind_Submission", "/-/Submission"]
                        for v in venue_list:
                            v = str(v).strip()
                            if not v:
                                continue
                            for suf in invitation_suffixes:
                                invita = f"{v}{suf}"
                                try:
                                    inv_params = {"limit": page_size, "offset": offset, "invitation": invita}
                                    logger.info("尝试基于 invitation 的回退请求: %s", inv_params)
                                    resp = client.get(notes_url, params=inv_params)
                                    resp.raise_for_status()
                                    fallback_payload = resp.json()
                                    break
                                except Exception:
                                    continue
                            if fallback_payload is not None:
                                break
                        if fallback_payload is None:
                            # 最后回退：尝试 POST /notes/search
                            search_url = f"{base_url}/notes/search"
                            post_bodies = [
                                {"limit": page_size, "offset": offset},
                            ]
                            # 如提供 venues，尝试基于 invitation 的 body
                            for v in venue_list:
                                v = str(v).strip()
                                if not v:
                                    continue
                                for suf in invitation_suffixes:
                                    post_bodies.append({"limit": page_size, "offset": offset, "invitation": f"{v}{suf}"})
                            # 如提供 query，尝试简单 term 字段
                            if query:
                                post_bodies.append({"limit": page_size, "offset": offset, "term": query})
                            for body in post_bodies:
                                try:
                                    logger.info("尝试 POST /notes/search 回退，body=%s", body)
                                    resp = client.post(search_url, json=body)
                                    resp.raise_for_status()
                                    fallback_payload = resp.json()
                                    break
                                except Exception:
                                    continue
                        if fallback_payload is None:
                            logger.warning("OpenReview 抓取失败（所有回退均失败）：%s", e2)
                            break
                        payload = fallback_payload
                else:
                    logger.warning("OpenReview 抓取失败：%s", he)
                    break
            except Exception as e:
                logger.warning("OpenReview 抓取失败：%s", e)
                break

            # 允许 payload 是 dict 或 list；若为空则认为已到末尾
            empty = False
            if isinstance(payload, dict):
                # 常见为 {'notes': [...], 'count': N} 或类似结构
                items = payload.get("notes") or payload.get("items") or []
                if not isinstance(items, list) or len(items) == 0:
                    empty = True
                page_payload = {
                    "source": "openreview",
                    "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
                    "payload": payload,
                }
            elif isinstance(payload, list):
                if len(payload) == 0:
                    empty = True
                page_payload = {
                    "source": "openreview",
                    "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
                    "payload": {"notes": payload},
                }
            else:
                logger.warning("OpenReview 返回未知结构，停止。类型=%s", type(payload))
                break

            if empty:
                break

            records.append(page_payload)
            fetched += page_size
            offset += page_size
            page += 1

    return records


