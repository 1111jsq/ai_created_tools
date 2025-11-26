"""SVG 验证器 - 提供基本的 SVG XML 格式验证"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_svg(svg_content: str) -> Tuple[bool, str]:
    """
    验证 SVG 内容是否符合基本的 XML 格式要求
    
    Args:
        svg_content: SVG XML 字符串
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not svg_content or not svg_content.strip():
        return False, "SVG 内容为空"
    
    # 检查是否包含 <svg> 标签
    if "<svg" not in svg_content and "<SVG" not in svg_content:
        return False, "SVG 内容缺少 <svg> 标签"
    
    try:
        # 尝试解析 XML
        # 注意：SVG 可能包含命名空间，使用 ElementTree 解析
        root = ET.fromstring(svg_content)
        
        # 检查根元素是否为 svg
        if root.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
            return False, f"根元素不是 svg，而是 {root.tag}"
        
        return True, ""
    except ET.ParseError as e:
        error_msg = f"XML 解析错误: {str(e)}"
        logger.warning("SVG 验证失败: %s", error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"验证过程出错: {str(e)}"
        logger.warning("SVG 验证异常: %s", error_msg)
        return False, error_msg


def extract_svg_content(text: str) -> str:
    """
    从文本中提取 SVG 代码块
    
    如果文本包含 ```svg 或 ```xml 代码块，提取其中的内容
    否则返回原文本
    
    Args:
        text: 可能包含代码块的文本
        
    Returns:
        提取的 SVG 内容
    """
    # 检查是否包含代码块
    if "```svg" in text:
        start = text.find("```svg") + 7
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    
    if "```xml" in text:
        start = text.find("```xml") + 7
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    
    if "```" in text:
        # 通用代码块，尝试提取
        parts = text.split("```")
        if len(parts) >= 3:
            # 取第一个代码块的内容
            return parts[1].strip()
    
    # 如果没有代码块标记，返回原文本
    return text.strip()

