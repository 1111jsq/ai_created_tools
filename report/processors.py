"""数据处理模块 - 论文和资讯处理"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .models import NewsAggItem, PaperItem


def extract_paper_details(
    papers: List[PaperItem],
    logger: logging.Logger,
    use_llm: bool,
) -> List[Dict[str, Any]]:
    """提取论文的功能和核心内容"""
    results = []
    
    def _extract_feature_from_title(title: str) -> str:
        """从标题中提取功能特性"""
        feature_keywords = {
            "多智能体": ["multi-agent", "multi-agent", "多智能体", "多代理"],
            "工具调用": ["tool", "工具", "inspectable tools"],
            "强化学习": ["reinforcement learning", "强化学习", "RL"],
            "意图识别": ["intent", "意图"],
            "语音交互": ["speech", "语音", "voice"],
            "架构": ["architecture", "架构", "framework", "框架"],
            "协作": ["collaboration", "协作", "cooperation"],
            "规划": ["planning", "规划"],
            "评估": ["evaluation", "评估", "benchmark"],
        }
        title_lower = title.lower()
        for feature, keywords in feature_keywords.items():
            if any(kw in title_lower for kw in keywords):
                return feature
        return "其他"
    
    def _extract_core_content_simple(title: str, tags: Optional[List[str]]) -> str:
        """简单提取核心内容（基于标题和标签）"""
        parts = []
        if tags:
            parts.extend(tags[:3])
        # 从标题中提取关键信息
        if "multi-agent" in title.lower() or "多智能体" in title:
            parts.append("多智能体架构")
        if "tool" in title.lower() or "工具" in title:
            parts.append("工具增强")
        if "reinforcement" in title.lower() or "强化学习" in title:
            parts.append("强化学习")
        return "、".join(parts[:3]) if parts else "智能体研究"
    
    if use_llm:
        # 使用LLM批量提取详细信息（提高效率）
        from common.llm import LLMClient
        client = LLMClient()
        if client.api_key:
            try:
                # 批量处理，减少API调用次数
                paper_titles = [p.title for p in papers]
                paper_tags = [p.tags for p in papers]
                
                prompt = "请分析以下论文标题列表，为每篇论文提取：1) 主要功能特性（如多智能体、工具调用、强化学习等）；2) 核心研究内容（一句话概括）。\n\n论文列表：\n"
                for i, (title, tags) in enumerate(zip(paper_titles, paper_tags), 1):
                    tags_str = ", ".join(tags[:3]) if tags else "无标签"
                    prompt += f"{i}. {title} [标签: {tags_str}]\n"
                
                prompt += "\n返回JSON格式，包含papers数组，每个元素包含：{\"feature\": \"功能名称\", \"core_content\": \"核心内容描述\"}"
                
                messages = [
                    {"role": "system", "content": "你是智能体研究领域的专家，请用中文回答。返回的JSON格式必须正确。"},
                    {"role": "user", "content": prompt},
                ]
                result = client.chat_json(messages=messages, model=None)
                
                # 解析批量结果
                papers_data = result.get("papers", [])
                if isinstance(papers_data, list) and len(papers_data) == len(papers):
                    for i, p in enumerate(papers):
                        paper_data = papers_data[i] if i < len(papers_data) else {}
                        feature = paper_data.get("feature", _extract_feature_from_title(p.title))
                        core_content = paper_data.get("core_content", _extract_core_content_simple(p.title, p.tags))
                        results.append({
                            "title": p.title,
                            "feature": feature,
                            "core_content": core_content,
                        })
                else:
                    # 如果批量处理失败，回退到简单方法
                    logger.warning("LLM批量提取论文详情格式不正确，使用简单方法")
                    use_llm = False
            except Exception as e:
                logger.warning("LLM提取论文详情失败，使用简单方法: %s", e)
                use_llm = False
    
    if not use_llm:
        # 使用简单方法
        for p in papers:
            feature = _extract_feature_from_title(p.title)
            core_content = _extract_core_content_simple(p.title, p.tags)
            results.append({
                "title": p.title,
                "feature": feature,
                "core_content": core_content,
            })
    
    return results


def count_products_in_news(news: List[NewsAggItem]) -> int:
    """统计资讯中涉及的产品数量"""
    products = set()
    product_keywords = [
        "GPT", "ChatGPT", "Claude", "Gemini", "MiMo", "灵光", "DreamGym",
        "Agent2Agent", "A2A", "MOSS", "NotebookLM", "Sora", "Grok",
        "LangChain", "LangGraph", "CrewAI", "AgentScope", "AutoGen"
    ]
    
    for n in news:
        title_lower = n.title.lower()
        for keyword in product_keywords:
            if keyword.lower() in title_lower:
                products.add(keyword)
    
    return len(products)


def identify_important_news(
    news: List[NewsAggItem],
    logger: logging.Logger,
    use_llm: bool,
) -> List[NewsAggItem]:
    """识别重要资讯"""
    important_keywords = [
        "发布", "开源", "重大", "突破", "首次", "里程碑", "重磅",
        "release", "open source", "major", "breakthrough", "first"
    ]
    
    if use_llm:
        from common.llm import LLMClient
        client = LLMClient()
        if client.api_key:
            try:
                titles = [n.title for n in news[:20]]
                prompt = f"请从以下资讯标题中识别出最重要的3-5条（涉及重大产品发布、技术突破、行业里程碑等）：\n\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
                prompt += "\n\n返回JSON格式，包含important_indices数组（从1开始的索引）：{\"important_indices\": [1, 3, 5]}"
                messages = [
                    {"role": "system", "content": "你是技术资讯分析师，请用中文回答。"},
                    {"role": "user", "content": prompt},
                ]
                result = client.chat_json(messages=messages, model=None)
                indices = result.get("important_indices", [])
                important = [news[i-1] for i in indices if 1 <= i <= len(news)]
                return important
            except Exception as e:
                logger.warning("LLM识别重要资讯失败，使用关键词方法: %s", e)
    
    # 使用关键词方法
    important = []
    for n in news:
        title_lower = n.title.lower()
        if any(kw in title_lower for kw in important_keywords):
            important.append(n)
    
    return important[:5]  # 最多返回5条

