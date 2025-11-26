"""SVG 生成器 CLI 入口"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .llm_service import SVGLLMService
from .svg_validator import validate_svg

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def read_input(input_arg: str) -> str:
    """
    读取输入内容（自然语言或文件路径）
    
    Args:
        input_arg: 输入参数（可能是文本或文件路径）
        
    Returns:
        任务描述文本
    """
    if os.path.exists(input_arg):
        # 是文件路径
        try:
            with open(input_arg, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.error("读取文件失败: %s", e)
            sys.exit(1)
    else:
        # 是自然语言文本
        return input_arg


def get_default_output_path() -> str:
    """生成默认输出路径（带时间戳）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / f"svg_output_{timestamp}.svg")


def save_svg(svg_content: str, output_path: str) -> None:
    """
    保存 SVG 内容到文件
    
    Args:
        svg_content: SVG XML 内容
        output_path: 输出文件路径
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path_obj, "w", encoding="utf-8") as f:
            f.write(svg_content)
        logger.info("SVG 文件已保存到: %s", output_path)
    except Exception as e:
        logger.error("保存 SVG 文件失败: %s", e)
        sys.exit(1)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="根据任务描述生成 SVG 图片（使用 LLM）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用自然语言描述
  python -m svg_generator.main "创建一个简单的流程图，包含开始、处理、结束三个节点"
  
  # 从文件读取任务描述
  python -m svg_generator.main task.txt
  
  # 指定输出路径
  python -m svg_generator.main "画一个架构图" --output diagrams/architecture.svg
        """,
    )
    
    parser.add_argument(
        "input",
        help="任务描述（自然语言文本或文件路径）",
    )
    parser.add_argument(
        "--output", "-o",
        help="输出 SVG 文件路径（默认: data/output/svg_output_<timestamp>.svg）",
    )
    parser.add_argument(
        "--api-key",
        help="LLM API Key（可选，会从 .env 文件读取）",
    )
    parser.add_argument(
        "--base-url",
        help="LLM API Base URL（可选，会从 .env 文件读取）",
    )
    parser.add_argument(
        "--model",
        help="LLM 模型名称（可选，会从 .env 文件读取）",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="LLM 温度参数（默认: 0.3）",
    )
    
    args = parser.parse_args()
    
    # 读取输入
    task_description = read_input(args.input)
    if not task_description:
        logger.error("任务描述为空")
        sys.exit(1)
    
    logger.info("任务描述: %s", task_description[:100] + ("..." if len(task_description) > 100 else ""))
    
    # 初始化 LLM 服务
    try:
        llm_service = SVGLLMService(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
        )
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)
    
    # 生成 SVG
    try:
        svg_content = llm_service.generate_svg(task_description, temperature=args.temperature)
    except Exception as e:
        logger.error("生成 SVG 失败: %s", e)
        sys.exit(1)
    
    # 验证 SVG
    is_valid, error_msg = validate_svg(svg_content)
    if not is_valid:
        logger.warning("SVG 验证失败: %s", error_msg)
        logger.warning("仍将保存文件，但可能无法正常渲染")
    else:
        logger.info("SVG 验证通过")
    
    # 确定输出路径
    output_path = args.output or get_default_output_path()
    
    # 保存文件
    save_svg(svg_content, output_path)
    
    print(f"\n✓ SVG 文件已生成: {output_path}")


if __name__ == "__main__":
    main()

