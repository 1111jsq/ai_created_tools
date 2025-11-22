from __future__ import annotations

import os
from typing import Any, Dict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEFAULT_SOURCES_PATH = os.path.join(PROJECT_ROOT, "configs", "sources.yaml")
DEFAULT_LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "app.log")


def get_sources_path() -> str:
    return os.environ.get("NEWS_SOURCES_PATH", DEFAULT_SOURCES_PATH)


def get_log_path() -> str:
    return os.environ.get("NEWS_LOG_PATH", DEFAULT_LOG_PATH)


def get_deepseek_config() -> Dict[str, Any]:
    return {
        "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
        "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "default_model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        "timeout": int(os.environ.get("DEEPSEEK_TIMEOUT", "60")),
    }
