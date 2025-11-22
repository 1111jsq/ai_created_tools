from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re

from agents_papers.config import OPENREVIEW_CONFIG

logger = logging.getLogger(__name__)


def _extract_note_minimal(note: Any) -> Dict[str, Any]:
    # note 结构来自 openreview-py v2；尽量用 getattr 宽容访问
    nid = getattr(note, "id", None) or getattr(note, "_id", None)
    forum = getattr(note, "forum", None) or getattr(note, "_forum", None) or nid
    content = getattr(note, "content", {}) or {}
    venue = getattr(note, "venue", None) or getattr(note, "venueid", None) or ""
    cdate = getattr(note, "cdate", None) or getattr(note, "tmdate", None) or None
    # 统一时间为 ISO 字符串（若存在毫秒 epoch）
    published = None
    if isinstance(cdate, (int, float)) and cdate > 0:
        try:
            dt = datetime.utcfromtimestamp(int(cdate) / 1000.0).replace(tzinfo=timezone.utc)
            published = dt.isoformat()
        except Exception:
            published = None
    return {
        "id": nid,
        "forum": forum,
        "content": content,
        "venue": venue,
        "published": published,
    }


def _derive_year_hint(label: str) -> Optional[str]:
    """
    从标签中粗略提取年份：支持 'YYYY-MM' 或 'YYYYMMDD-YYYYMMDD' 形式。
    """
    if not label:
        return None
    m = re.search(r"(20\d{2})", label)
    return m.group(1) if m else None


def _list_recent_venues(client: Any, year_hint: Optional[str]) -> List[str]:
    try:
        venues_group = client.get_group(id="venues")
        members = list(getattr(venues_group, "members", []) or [])
        if year_hint:
            members = [v for v in members if year_hint in v]
        return members
    except Exception:
        return []


def fetch_openreview_v2_raw(
    month: str,
    venue_id: Optional[str],
    status: str = "all",
    limit: int = 300,
) -> List[Dict[str, Any]]:
    """
    使用 openreview-py v2 客户端抓取公开论文。若未安装或调用失败，返回空列表。
    """
    if not OPENREVIEW_CONFIG.get("enabled", False):
        logger.info("OpenReview v2 未启用（设置 OPENREVIEW_ENABLED=1 可开启）")
        return []
    if not venue_id:
        try:
            import openreview
            client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
            year_hint = _derive_year_hint(month)
            candidates = _list_recent_venues(client, year_hint)
            if candidates:
                show = candidates[:10]
                logger.info("OpenReview v2 需要提供 OPENREVIEW_VENUE_ID，例如（前10条）：%s", ", ".join(show))
            else:
                logger.info("OpenReview v2 需要提供 OPENREVIEW_VENUE_ID，未能列出候选。请在 OpenReview 会议主页 URL 的 group?id= 后复制。")
        except Exception:
            logger.info("OpenReview v2 需要提供 OPENREVIEW_VENUE_ID，且需要安装 openreview-py。")
        return []

    try:
        import openreview
    except Exception as e:
        logger.warning("未安装 openreview-py 或导入失败：%s", e)
        return []

    try:
        client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
        venue_group = client.get_group(venue_id)
        # API 版本提示
        if hasattr(venue_group, "domain") and getattr(venue_group, "domain") is not None:
            logger.info("'%s' 使用 API v2", venue_id)
        else:
            logger.info("'%s' 可能使用旧版 API（v1），将尝试通用检索。", venue_id)

        # 规范化期望状态（支持 published/final → accepted）
        s = (status or "all").strip().lower()
        if s in ("published", "final"):
            s = "accepted"

        notes: List[Any] = []
        if s == "all":
            sub_name = venue_group.content["submission_name"]["value"]
            invitation = f"{venue_id}/-/{sub_name}"
            notes = client.get_all_notes(invitation=invitation)
        else:
            # 优先从 group.content 中读取 {status}_venue_id；accepted 缺失时尝试通用 venue_id
            status_key = f"{s}_venue_id"
            status_venueid = (venue_group.content.get(status_key, {}) or {}).get("value")
            if not status_venueid and s == "accepted":
                status_venueid = (venue_group.content.get("venue_id", {}) or {}).get("value")
            if not status_venueid and s == "rejected":
                # 常见键名变体
                for k in ("rejected_venue_id", "desk_rejected_venue_id"):
                    status_venueid = (venue_group.content.get(k, {}) or {}).get("value")
                    if status_venueid:
                        break

            if status_venueid:
                notes = client.get_all_notes(content={"venueid": status_venueid})
                # 保险起见再做一次客户端过滤，确保只保留最终发表（或指定状态）的 venueid
                if s in ("accepted",):
                    target_vids = {status_venueid, venue_id}
                    notes = [n for n in notes if getattr(n, "venueid", None) in target_vids]
            else:
                logger.info("未找到状态 %s 对应的 venueid，回退为 all", s)
                sub_name = venue_group.content["submission_name"]["value"]
                invitation = f"{venue_id}/-/{sub_name}"
                notes = client.get_all_notes(invitation=invitation)

        # 限制最大数量（简单截断）
        if isinstance(notes, list) and limit and len(notes) > limit:
            notes = notes[:limit]

        # 打包为统一 raw 记录（单页）
        items = [_extract_note_minimal(n) for n in notes]
        record = {
            "source": "openreview",
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
            "payload": {"notes": items},
        }
        return [record] if items else []
    except Exception as e:
        logger.warning("OpenReview v2 抓取失败：%s", e)
        return []


