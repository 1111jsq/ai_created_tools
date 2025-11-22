"""
配置文件：管理代理、路径、GitHub 与 DeepSeek 配置。
密钥通过环境变量读取，避免硬编码。
"""
import os
from typing import Dict, Any
os.environ.setdefault('HTTP_PROXY', 'http://proxyhk.zte.com.cn:80')
os.environ.setdefault('HTTPS_PROXY', 'http://proxyhk.zte.com.cn:80')
# 代理设置（可选，通过环境变量控制）
HTTP_PROXY = os.environ.get('HTTP_PROXY')
HTTPS_PROXY = os.environ.get('HTTPS_PROXY')
if HTTP_PROXY:
    os.environ['HTTP_PROXY'] = HTTP_PROXY
if HTTPS_PROXY:
    os.environ['HTTPS_PROXY'] = HTTPS_PROXY

# DeepSeek API 配置（密钥从环境变量读取）
DEEPSEEK_CONFIG: Dict[str, Any] = {
    'api_key': os.environ.get('DEEPSEEK_API_KEY', 'sk-ad455333bb704d76b845ebc19150df5d'),
    'base_url': os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
    'default_model': os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),  # 或 'deepseek-reasoner'
    'timeout': int(os.environ.get('DEEPSEEK_TIMEOUT', '60')),
}

# GitHub API 配置
GITHUB_CONFIG: Dict[str, Any] = {
    'base_url': os.environ.get('GITHUB_API_BASE', 'https://api.github.com'),
    'per_page': int(os.environ.get('GITHUB_API_PER_PAGE', '100')),
    'max_pages': int(os.environ.get('GITHUB_API_MAX_PAGES', '10')),
}

# 项目路径配置
PROJECT_PATHS: Dict[str, str] = {
    'src_dir': os.environ.get('SRC_DIR', 'src'),
    'data_dir': os.environ.get('DATA_DIR', 'data'),
    'releases_dir': os.environ.get('RELEASES_DIR', 'data/releases'),
    'summaries_dir': os.environ.get('SUMMARIES_DIR', 'data/summaries'),
}

# 爬虫配置
CRAWLER_CONFIG: Dict[str, Any] = {
    'request_delay': float(os.environ.get('CRAWLER_REQUEST_DELAY', '1.0')),
    'timeout': int(os.environ.get('CRAWLER_TIMEOUT', '30')),
    'retry_times': int(os.environ.get('CRAWLER_RETRY_TIMES', '3')),
}

# 大模型配置
LLM_CONFIG: Dict[str, Any] = {
    'max_tokens': int(os.environ.get('LLM_MAX_TOKENS', '2000')),
    'temperature': float(os.environ.get('LLM_TEMPERATURE', '0.7')),
    'timeout': int(os.environ.get('LLM_TIMEOUT', '60')),
    # 分段摘要参数（按字符粗略控制，以避免超出上下文）
    'chunk_chars': int(os.environ.get('LLM_CHUNK_CHARS', '12000')),
    'chunk_overlap': int(os.environ.get('LLM_CHUNK_OVERLAP', '500')),
    # 按版本标题(##)分组的块大小
    'versions_per_chunk': int(os.environ.get('LLM_VERSIONS_PER_CHUNK', '20')),
    # 是否在切分前进行关键词预筛选（会丢弃无关键词的小节）。默认关闭以避免丢失版本。
    'pre_filter': os.environ.get('LLM_PRE_FILTER', 'false').lower() == 'true',
}

# 文件编码
ENCODING = os.environ.get('FILE_ENCODING', 'utf-8')

