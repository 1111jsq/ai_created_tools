"""
配置文件：统一从项目根目录的 .env 文件读取配置。
"""
import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入 common.config_loader
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from common.config_loader import load_env_config

# 确保加载 .env 文件
load_env_config()

__all__ = []

