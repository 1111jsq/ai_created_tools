"""图片生成模块"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from .models import ImageGenerationRequest, NewsAggItem, PaperItem, ReleaseAggItem


def build_image_judge_prompt(
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
    daily_counts: Dict[str, Dict[str, int]],
) -> str:
    """构建图片判断的 prompt，重点关注智能体功能、公司产品等深度信息"""
    def _clip(txt: str, n: int = 150) -> str:
        return (txt or "")[:n]
    
    def _extract_company_from_title(title: str) -> str:
        """从标题中提取可能的公司名称"""
        companies = ["OpenAI", "Meta", "Google", "微软", "小米", "蚂蚁", "Elastic", "Grok", "MOSS", "NotebookLM"]
        for company in companies:
            if company.lower() in title.lower():
                return company
        return ""
    
    def _extract_agent_features(title: str) -> List[str]:
        """从标题中提取智能体功能特性"""
        features = []
        feature_keywords = {
            "多智能体": ["multi-agent", "multi-agent", "多智能体", "多代理"],
            "工具调用": ["tool", "工具", "inspectable tools"],
            "强化学习": ["reinforcement learning", "强化学习", "RL"],
            "意图识别": ["intent", "意图"],
            "语音交互": ["speech", "语音", "voice"],
            "架构": ["architecture", "架构", "framework", "框架"],
            "协作": ["collaboration", "协作", "cooperation"],
        }
        title_lower = title.lower()
        for feature, keywords in feature_keywords.items():
            if any(kw in title_lower for kw in keywords):
                features.append(feature)
        return features
    
    parts = [
        "这是一份智能体领域的深度洞察报告，请分析以下内容，重点关注智能体功能、公司产品发布、技术趋势等深度信息：",
        "",
        "【数据概览】",
        f"- 论文: {len(papers)} 条",
        f"- 资讯: {len(news)} 条",
        f"- SDK 更新: {len(releases)} 条",
        "",
    ]
    
    # 分析论文中的智能体功能
    if papers:
        parts.append("【论文分析 - 智能体功能特性】")
        feature_count = {}
        for p in papers:
            features = _extract_agent_features(p.title)
            for f in features:
                feature_count[f] = feature_count.get(f, 0) + 1
        
        if feature_count:
            parts.append("智能体功能分布：")
            for feature, count in sorted(feature_count.items(), key=lambda x: x[1], reverse=True):
                parts.append(f"  - {feature}: {count} 篇论文")
        parts.append("")
        
        parts.append("【论文详细列表（前 15 条）】")
        for p in papers[:15]:
            company = _extract_company_from_title(p.title)
            features = _extract_agent_features(p.title)
            feature_str = f" [功能: {', '.join(features)}]" if features else ""
            company_str = f" [公司: {company}]" if company else ""
            parts.append(f"- {_clip(p.title)}{company_str}{feature_str}")
        parts.append("")
    
    # 分析资讯中的公司产品发布
    if news:
        parts.append("【资讯分析 - 公司产品发布】")
        company_products = {}
        for n in news:
            company = _extract_company_from_title(n.title)
            if company:
                company_products[company] = company_products.get(company, 0) + 1
        
        if company_products:
            parts.append("各公司产品发布数量：")
            for company, count in sorted(company_products.items(), key=lambda x: x[1], reverse=True):
                parts.append(f"  - {company}: {count} 条资讯")
        parts.append("")
        
        parts.append("【资讯详细列表（前 20 条）】")
        for n in news[:20]:
            company = _extract_company_from_title(n.title)
            company_str = f" [公司: {company}]" if company else ""
            tags_str = f" [标签: {', '.join(n.tags[:3])}]" if n.tags else ""
            parts.append(f"- {_clip(n.title)}{company_str}{tags_str} [{_clip(n.source)}]")
        parts.append("")
    
    # 分析 SDK 更新中的框架活跃度
    if releases:
        parts.append("【SDK 更新分析 - 框架活跃度】")
        repo_updates = {}
        for r in releases:
            repo_updates[r.repo] = repo_updates.get(r.repo, 0) + 1
        
        if repo_updates:
            parts.append("各框架更新次数：")
            for repo, count in sorted(repo_updates.items(), key=lambda x: x[1], reverse=True):
                parts.append(f"  - {repo}: {count} 次更新")
        parts.append("")
        
        parts.append("【SDK 更新详细列表（前 15 条）】")
        for r in releases[:15]:
            parts.append(f"- {_clip(r.repo)} {_clip(r.tag)} {_clip(r.name)}")
        parts.append("")
    
    # 分析技术趋势关键词
    all_titles = [p.title for p in papers[:10]] + [n.title for n in news[:15]]
    trend_keywords = {
        "多智能体": 0,
        "语音": 0,
        "开源": 0,
        "框架": 0,
        "工具": 0,
        "强化学习": 0,
    }
    for title in all_titles:
        title_lower = title.lower()
        for keyword in trend_keywords:
            if keyword in title_lower:
                trend_keywords[keyword] += 1
    
    if any(trend_keywords.values()):
        parts.append("【技术趋势关键词统计】")
        for keyword, count in sorted(trend_keywords.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                parts.append(f"  - {keyword}: {count} 次提及")
        parts.append("")
    
    parts.append("请根据以上内容，重点关注智能体功能特性、公司产品发布、技术趋势等深度信息，")
    parts.append("生成能够反映业界趋势和现状的图片建议，避免简单的总数统计。")
    parts.append("返回 JSON 格式的判断结果。")
    
    return "\n".join(parts)


def judge_image_generation(
    papers: List[PaperItem],
    news: List[NewsAggItem],
    releases: List[ReleaseAggItem],
    daily_counts: Dict[str, Dict[str, int]],
    logger: logging.Logger,
) -> List[ImageGenerationRequest]:
    """
    使用 LLM 判断哪些内容适合生成图片
    
    Returns:
        图片生成请求列表，按优先级排序，最多 5 个
    """
    # 确保配置已加载
    from common.config_loader import load_env_config, get_env
    load_env_config()
    
    from common.llm import LLMClient
    
    client = LLMClient()
    if not client.api_key:
        logger.info("未配置 LLM_API_KEY，跳过图片生成判断")
        return []
    
    logger.info("开始使用 LLM 判断需要生成的图片...")
    
    try:
        # 构建判断 prompt
        prompt = build_image_judge_prompt(papers, news, releases, daily_counts)
        
        system_prompt = (
            "你是一位专业的智能体行业分析师和数据可视化专家。"
            "这是一份智能体领域的深度洞察报告，需要生成能够反映业界趋势和现状的图片。"
            "\n"
            "请分析报告内容，重点关注以下方面："
            "1. **智能体功能特性**：从论文和新闻中提取智能体的具体功能（如多智能体协作、工具调用、强化学习、意图识别等）"
            "2. **公司产品发布**：统计各公司（如 OpenAI、Meta、小米、蚂蚁等）发布的产品数量、类型分布"
            "3. **技术架构演进**：展示智能体架构的发展趋势（如多智能体架构、工具增强型LLM、语音交互等）"
            "4. **行业应用分布**：分析智能体在不同领域的应用（金融、医疗、教育、内容创作等）"
            "5. **开源生态活跃度**：展示各开源框架的更新频率、功能迭代等"
            "\n"
            "**重要**：不要生成简单的总数统计图表（如论文总数、新闻总数等），而要关注："
            "- 智能体功能类型的分布和趋势"
            "- 各公司/机构的产品发布活跃度"
            "- 技术方向的演进路径"
            "- 行业应用的深度和广度"
            "\n"
            "返回 JSON 格式的判断结果，包含以下字段："
            "- images: 图片建议列表，每个建议包含："
            "  - image_type: 图片类型（如 'bar_chart', 'pie_chart', 'architecture_diagram', 'timeline', 'network_diagram' 等）"
            "  - description: 图片生成的任务描述（自然语言，详细描述需要展示的内容，包括具体的数据、公司名称、功能名称等）"
            "  - suggested_position: 建议插入位置（如 'after_overview', 'in_insights', 'after_papers', 'after_news', 'after_sdk'）"
            "  - priority: 优先级（1-5，数字越大优先级越高）"
            "\n"
            "要求："
            "1. 最多返回 5 个图片建议"
            "2. 优先考虑能反映智能体行业深度洞察的内容"
            "3. description 要非常具体，包含公司名称、产品名称、功能特性、数据等细节"
            "4. 使用中文描述"
            "\n"
            "返回格式示例："
            '{"images": [{"image_type": "bar_chart", "description": "展示各公司智能体产品发布数量对比：OpenAI发布2个产品（GPT-5、教师专属ChatGPT），Meta发布1个产品（DreamGym框架），小米发布1个产品（MiMo-Embodied），蚂蚁发布1个产品（灵光），使用柱状图展示", "suggested_position": "after_news", "priority": 5}]}'
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        result = client.chat_json(messages=messages, model=None)
        
        # 解析结果
        images_data = result.get("images", [])
        if not isinstance(images_data, list):
            logger.warning("LLM 返回的 images 格式不正确")
            return []
        
        # 转换为 ImageGenerationRequest 列表
        requests: List[ImageGenerationRequest] = []
        for img_data in images_data:
            try:
                req = ImageGenerationRequest(
                    image_type=img_data.get("image_type", ""),
                    description=img_data.get("description", ""),
                    suggested_position=img_data.get("suggested_position", ""),
                    priority=int(img_data.get("priority", 1)),
                )
                if req.description and req.image_type:
                    requests.append(req)
            except Exception as e:
                logger.warning("解析图片建议失败: %s, %s", img_data, e)
                continue
        
        # 按优先级排序，取前 5 个
        requests.sort(key=lambda x: x.priority, reverse=True)
        requests = requests[:5]
        
        logger.info("LLM 判断完成，建议生成 %d 张图片", len(requests))
        for i, req in enumerate(requests, 1):
            logger.info("  图片 %d: 类型=%s, 位置=%s, 优先级=%d, 描述=%s", 
                       i, req.image_type, req.suggested_position, req.priority, req.description[:50])
        return requests
        
    except Exception as e:
        logger.exception("LLM 图片判断失败，跳过图片生成: %s", e)
        return []


def generate_svg_image(
    description: str,
    output_path: Path,
    logger: logging.Logger,
) -> str | None:
    """
    使用 svg_generator 生成 SVG 图片
    
    Args:
        description: 图片生成的任务描述
        output_path: 输出文件路径
        logger: 日志记录器
        
    Returns:
        生成的图片相对路径（相对于报告目录），失败返回 None
    """
    try:
        # 确保配置已加载
        from common.config_loader import load_env_config
        load_env_config()
        
        # 导入 svg_generator 模块
        import sys
        from pathlib import Path as PathLib
        
        # 获取项目根目录
        project_root = PathLib(__file__).parent.parent
        
        # 确保项目根目录在路径中（用于导入 common 模块和 svg_generator 包）
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # 使用包导入方式，这样相对导入可以正常工作
        # svg_generator 是一个包，src 是它的子包
        from svg_generator.src.llm_service import SVGLLMService
        
        # 初始化 SVG 生成服务（会自动从环境变量读取配置）
        logger.info("初始化 SVG 生成服务...")
        svg_service = SVGLLMService()
        
        # 生成 SVG
        logger.info("生成 SVG 图片: %s", description[:50])
        svg_content = svg_service.generate_svg(description, temperature=0.3)
        
        if not svg_content or not svg_content.strip():
            logger.warning("SVG 生成返回空内容")
            return None
        
        # 保存到文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(svg_content, encoding="utf-8")
        
        logger.info("SVG 图片已保存: %s", str(output_path))
        
        # 返回相对路径
        return output_path.name
        
    except ValueError as e:
        # API Key 未配置
        logger.warning("SVG 生成失败（API Key 未配置）: %s", e)
        return None
    except ImportError as e:
        logger.exception("导入 SVG 生成模块失败: %s", e)
        return None
    except Exception as e:
        logger.exception("SVG 生成失败: %s", e)
        return None


def generate_images_and_insert(
    reports_dir: Path,
    image_requests: List[ImageGenerationRequest],
    logger: logging.Logger,
) -> Dict[str, str]:
    """
    生成图片并返回插入位置映射
    
    Args:
        reports_dir: 报告输出目录
        image_requests: 图片生成请求列表
        logger: 日志记录器
        
    Returns:
        位置到图片路径的映射，如 {"after_overview": "assets/image_1.svg"}
    """
    if not image_requests:
        return {}
    
    # 创建 assets 目录
    assets_dir = reports_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    position_to_image: Dict[str, str] = {}
    image_index = 1
    
    for req in image_requests:
        try:
            # 生成图片文件名
            image_filename = f"image_{image_index}.svg"
            image_path = assets_dir / image_filename
            
            logger.info("开始生成图片 %d/%d: %s", image_index, len(image_requests), req.description[:50])
            
            # 生成 SVG
            relative_path = generate_svg_image(
                description=req.description,
                output_path=image_path,
                logger=logger,
            )
            
            if relative_path:
                # 保存映射关系（使用相对路径，相对于报告文件）
                relative_to_report = f"assets/{relative_path}"
                # 检查文件是否真的存在
                if image_path.exists() and image_path.stat().st_size > 0:
                    position_to_image[req.suggested_position] = relative_to_report
                    image_index += 1
                    logger.info("✓ 图片生成成功，位置: %s, 路径: %s", req.suggested_position, relative_to_report)
                else:
                    logger.warning("✗ 图片文件不存在或为空，跳过: %s", image_path)
            else:
                logger.warning("✗ 图片生成失败，跳过: %s", req.description[:50])
                
        except Exception as e:
            logger.exception("生成图片时出错: %s", e)
            continue
    
    logger.info("图片生成完成，共生成 %d 张图片", len(position_to_image))
    return position_to_image

