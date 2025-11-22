"""
配置文件：管理代理、路径、GitHub 与 DeepSeek 配置。
密钥与代理仅通过环境变量读取，避免任何硬编码。
"""
import os
from typing import Dict, Any

# 注意：不强制设置代理，完全依赖用户环境中的 HTTP_PROXY/HTTPS_PROXY

# DeepSeek/OpenAI API 配置（仅从环境变量读取；未设置则视为不可用）
DEEPSEEK_CONFIG: Dict[str, Any] = {
    'api_key': os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY') or '',
    'base_url': os.getenv('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com',
    'default_model': os.getenv('DEEPSEEK_DEFAULT_MODEL') or 'deepseek-chat',  # 可切换为 'deepseek-reasoner'
}

# GitHub API 配置
GITHUB_CONFIG: Dict[str, Any] = {
    'base_url': 'https://api.github.com',
    'per_page': int(os.getenv('GITHUB_PER_PAGE', '100')),
    'max_pages': int(os.getenv('GITHUB_MAX_PAGES', '10')),
}

# 项目路径配置
PROJECT_PATHS: Dict[str, str] = {
    'src_dir': 'src',
    'data_dir': 'data',
    'releases_dir': 'data/releases',
    'summaries_dir': 'data/summaries',
}

# 爬虫配置
CRAWLER_CONFIG: Dict[str, Any] = {
    'request_delay': float(os.getenv('CRAWLER_REQUEST_DELAY', '1.0')),
    'timeout': int(os.getenv('CRAWLER_TIMEOUT', '30')),
    'retry_times': int(os.getenv('CRAWLER_RETRY_TIMES', '3')),
}

# 大模型配置
LLM_CONFIG: Dict[str, Any] = {
    'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '2000')),
    'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
    'timeout': int(os.getenv('LLM_TIMEOUT', '60')),
    # 分段摘要参数（按字符粗略控制，以避免超出上下文）
    'chunk_chars': int(os.getenv('LLM_CHUNK_CHARS', '12000')),
    'chunk_overlap': int(os.getenv('LLM_CHUNK_OVERLAP', '500')),
    # 按版本标题(##)分组的块大小
    'versions_per_chunk': int(os.getenv('LLM_VERSIONS_PER_CHUNK', '20')),
    # 是否在切分前进行关键词预筛选（会丢弃无关键词的小节）。默认关闭以避免丢失版本。
    'pre_filter': os.getenv('LLM_PRE_FILTER', 'false').lower() == 'true',
}

# 文件编码
ENCODING = 'utf-8'
 
