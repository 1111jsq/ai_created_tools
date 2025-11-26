"""
配置文件：管理代理、路径、GitHub 与 DeepSeek 配置。
统一从项目根目录的 .env 文件读取配置。
"""
import sys
from pathlib import Path
from typing import Dict, Any
import os

# 添加项目根目录到路径，以便导入 common.config_loader
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from common.config_loader import get_env, load_env_config

# 确保加载 .env 文件
load_env_config()

# 代理设置（从 .env 文件读取，可选）
HTTP_PROXY = get_env('HTTP_PROXY')
HTTPS_PROXY = get_env('HTTPS_PROXY')
if HTTP_PROXY:
    os.environ['HTTP_PROXY'] = HTTP_PROXY
if HTTPS_PROXY:
    os.environ['HTTPS_PROXY'] = HTTPS_PROXY

# LLM API 配置（从 .env 文件读取）
DEEPSEEK_CONFIG: Dict[str, Any] = {
    'api_key': get_env('LLM_API_KEY') or '',
    'base_url': get_env('LLM_BASE_URL', 'https://api.deepseek.com'),
    'default_model': get_env('LLM_MODEL', 'deepseek-chat'),
    'timeout': get_env('LLM_TIMEOUT', 60, int),
}

# GitHub API 配置
GITHUB_CONFIG: Dict[str, Any] = {
    'base_url': get_env('GITHUB_API_BASE', 'https://api.github.com'),
    'per_page': get_env('GITHUB_API_PER_PAGE', 100, int) or get_env('GITHUB_PER_PAGE', 100, int),
    'max_pages': get_env('GITHUB_API_MAX_PAGES', 10, int) or get_env('GITHUB_MAX_PAGES', 10, int),
}

# 项目路径配置
PROJECT_PATHS: Dict[str, str] = {
    'src_dir': get_env('SRC_DIR', 'src'),
    'data_dir': get_env('DATA_DIR', 'data'),
    'releases_dir': get_env('RELEASES_DIR', 'data/releases'),
    'summaries_dir': get_env('SUMMARIES_DIR', 'data/summaries'),
}

# 爬虫配置
CRAWLER_CONFIG: Dict[str, Any] = {
    'request_delay': get_env('CRAWLER_REQUEST_DELAY', 1.0, float),
    'timeout': get_env('CRAWLER_TIMEOUT', 30, int),
    'retry_times': get_env('CRAWLER_RETRY_TIMES', 3, int),
}

# 大模型配置
LLM_CONFIG: Dict[str, Any] = {
    'max_tokens': get_env('LLM_MAX_TOKENS', 2000, int),
    'temperature': get_env('LLM_TEMPERATURE', 0.7, float),
    'timeout': get_env('LLM_TIMEOUT', 60, int),
    # 分段摘要参数（按字符粗略控制，以避免超出上下文）
    'chunk_chars': get_env('LLM_CHUNK_CHARS', 12000, int),
    'chunk_overlap': get_env('LLM_CHUNK_OVERLAP', 500, int),
    # 按版本标题(##)分组的块大小
    'versions_per_chunk': get_env('LLM_VERSIONS_PER_CHUNK', 20, int),
    # 是否在切分前进行关键词预筛选（会丢弃无关键词的小节）。默认关闭以避免丢失版本。
    'pre_filter': get_env('LLM_PRE_FILTER', False, bool),
}

# 文件编码
ENCODING = get_env('FILE_ENCODING', 'utf-8')

