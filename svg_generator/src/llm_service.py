"""LLM 服务 - 使用 LLM 生成 SVG 代码"""

from __future__ import annotations

import logging
import sys
import os
from typing import Optional

# 添加项目根目录到路径，以便导入 common 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from common.llm import LLMClient
from .svg_validator import extract_svg_content

logger = logging.getLogger(__name__)


class SVGLLMService:
    """使用 LLM 生成 SVG 代码的服务"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """
        初始化 LLM 服务
        
        Args:
            api_key: LLM API Key（可选，会从环境变量读取）
            base_url: LLM API Base URL（可选，会从环境变量读取）
            model: LLM 模型名称（可选，会从环境变量读取）
        """
        self.client = LLMClient(api_key=api_key, base_url=base_url, model=model)
        
        if not self.client.api_key:
            raise ValueError(
                "未提供 LLM_API_KEY。请在 .env 文件中配置 LLM_API_KEY，"
                "或在命令行中通过 --api-key 参数提供。"
            )
    
    def generate_svg(self, task_description: str, temperature: float = 0.3) -> str:
        """
        根据任务描述生成 SVG 代码
        
        Args:
            task_description: 任务描述（自然语言）
            temperature: LLM 温度参数（默认 0.3，较低值以获得更稳定的输出）
            
        Returns:
            生成的 SVG XML 代码
        """
        system_prompt = (
            "你是一位专业的 SVG 图形设计师。"
            "请根据用户的任务描述，生成符合 SVG 1.1 规范的 XML 代码。\n\n"
            "要求：\n"
            "1. 生成的代码必须是有效的 SVG XML，包含必要的命名空间和属性\n"
            "2. 代码应该可以直接在浏览器中渲染\n"
            "3. 使用合适的尺寸（建议 width 和 height 在 400-800 之间）\n"
            "4. 使用清晰的样式和颜色\n"
            "5. 如果是流程图或架构图，确保节点和连线布局合理\n"
            "6. 直接输出 SVG 代码，不要包含 markdown 代码块标记（如 ```svg）\n"
            "7. 如果用户要求特定类型的图表（流程图、架构图、数据图表等），请生成对应的 SVG\n\n"
            "请直接输出 SVG XML 代码，不要添加任何解释文字。"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description},
        ]
        
        try:
            logger.info("调用 LLM 生成 SVG 代码...")
            content = self.client.chat(messages=messages, temperature=temperature)
            
            if not content or not content.strip():
                raise ValueError("LLM 返回内容为空")
            
            # 从返回内容中提取 SVG 代码
            svg_content = extract_svg_content(content)
            
            logger.info("SVG 代码生成成功，长度: %d 字符", len(svg_content))
            return svg_content
            
        except Exception as e:
            logger.exception("LLM 生成 SVG 失败: %s", e)
            raise

