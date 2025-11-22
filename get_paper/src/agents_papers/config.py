"""
配置文件：仅保留当前实际用到的配置项（OpenReview）。
"""
import os
from typing import Dict, Any

# OpenReview API 配置（通过环境变量启用）
# OPENREVIEW_ENABLED=1 开启；可选 OPENREVIEW_BASE_URL、OPENREVIEW_PAGE_SIZE、OPENREVIEW_MAX_PAGES
OPENREVIEW_CONFIG: Dict[str, Any] = {
    'enabled': os.getenv('OPENREVIEW_ENABLED', '1') == '1',
    'base_url': os.getenv('OPENREVIEW_BASE_URL', 'https://api.openreview.net'),
    'page_size': int(os.getenv('OPENREVIEW_PAGE_SIZE', '50')),
    'max_pages': int(os.getenv('OPENREVIEW_MAX_PAGES', '4')),
    # 可选：限制会议；逗号分隔，如 "ICLR,NeurIPS"
    'venues': [v.strip() for v in os.getenv('OPENREVIEW_VENUES', '').split(',') if v.strip()],
    # 可选：简单检索词（标题/摘要），如 "agent OR tool use"
    'query': os.getenv('OPENREVIEW_QUERY', ''),
    'timeout': int(os.getenv('OPENREVIEW_TIMEOUT', '30')),
    # v2 客户端配置
    'venue_id': os.getenv('OPENREVIEW_VENUE_ID', ''),
    'status': os.getenv('OPENREVIEW_STATUS', 'all'),  # all | under_review | withdrawn | desk_rejected | accepted | rejected | published(final)
}

__all__ = ["OPENREVIEW_CONFIG"]

