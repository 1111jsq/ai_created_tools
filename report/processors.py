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
                prompt = "请分析以下论文信息，为每篇论文提取：\n1) 主要功能特性（如多智能体、工具调用、强化学习等）\n2) 核心研究内容（200-250字，包含关键贡献、创新点、应用场景）\n\n论文列表：\n"
                for i, p in enumerate(papers, 1):
                    # 构建完整的论文信息
                    authors_str = ""
                    if p.authors:
                        if isinstance(p.authors, list):
                            authors_str = ", ".join(p.authors[:3])
                        else:
                            authors_str = str(p.authors)
                    
                    tags_str = ", ".join(p.tags[:5]) if p.tags else "无标签"
                    rank_str = f"排名: {p.rank}" if p.rank else ""
                    score_str = f"评分: {p.score:.2f}" if p.score else ""
                    pub_str = f"发布时间: {p.published_at[:10]}" if p.published_at and len(p.published_at) >= 10 else ""
                    
                    info_parts = [p.title]
                    if authors_str:
                        info_parts.append(f"作者: {authors_str}")
                    if tags_str:
                        info_parts.append(f"标签: {tags_str}")
                    if pub_str:
                        info_parts.append(pub_str)
                    if rank_str:
                        info_parts.append(rank_str)
                    if score_str:
                        info_parts.append(score_str)
                    
                    prompt += f"{i}. {' | '.join(info_parts)}\n"
                
                prompt += "\n返回JSON格式，包含papers数组，每个元素包含：{\"feature\": \"功能名称\", \"core_content\": \"核心内容描述（200-250字，包含关键贡献、创新点、应用场景）\"}"
                
                messages = [
                    {"role": "system", "content": "你是智能体研究领域的专家，请用中文回答。返回的JSON格式必须正确。核心内容描述应详细说明论文的关键贡献、创新点、应用场景和技术方法，长度控制在200-250字。"},
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
                        # 确保核心内容不超过250字符
                        if len(core_content) > 250:
                            core_content = core_content[:247] + "..."
                        
                        # 格式化作者信息
                        authors_display = ""
                        if p.authors:
                            if isinstance(p.authors, list):
                                authors_list = p.authors[:3]
                                authors_display = ", ".join(authors_list)
                                if len(p.authors) > 3:
                                    authors_display += " 等"
                            else:
                                authors_display = str(p.authors)
                        
                        # 格式化发布时间
                        published_display = ""
                        if p.published_at:
                            try:
                                # 尝试提取日期部分（YYYY-MM-DD）
                                if len(p.published_at) >= 10:
                                    published_display = p.published_at[:10]
                            except Exception:
                                pass
                        
                        results.append({
                            "title": p.title,
                            "feature": feature,
                            "core_content": core_content,
                            "authors": authors_display,
                            "published_at": published_display,
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
            
            # 格式化作者信息
            authors_display = ""
            if p.authors:
                if isinstance(p.authors, list):
                    authors_list = p.authors[:3]
                    authors_display = ", ".join(authors_list)
                    if len(p.authors) > 3:
                        authors_display += " 等"
                else:
                    authors_display = str(p.authors)
            
            # 格式化发布时间
            published_display = ""
            if p.published_at:
                try:
                    if len(p.published_at) >= 10:
                        published_display = p.published_at[:10]
                except Exception:
                    pass
            
            results.append({
                "title": p.title,
                "feature": feature,
                "core_content": core_content,
                "authors": authors_display,
                "published_at": published_display,
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


def extract_products_from_news(
    news: List[NewsAggItem],
    logger: logging.Logger,
    use_llm: bool = False,
) -> Dict[str, List[str]]:
    """从资讯中提取涉及的产品信息
    
    Returns:
        Dict[str, List[str]]: 标题到产品列表的映射，每个标题最多2个主要产品
    """
    title_to_products: Dict[str, List[str]] = {}
    
    # 产品关键词库（产品名称 -> 关键词列表）
    product_keywords = {
        "OpenAI": ["OpenAI", "GPT", "ChatGPT", "GPT-4", "GPT-5", "Sora"],
        "Anthropic": ["Anthropic", "Claude"],
        "Google": ["Google", "Gemini", "NotebookLM", "Bard"],
        "Meta": ["Meta", "Facebook", "DreamGym", "Llama"],
        "Microsoft": ["Microsoft", "微软", "Copilot", "Azure"],
        "小米": ["小米", "MiMo", "MiMo-Embodied", "Xiaomi"],
        "蚂蚁": ["蚂蚁", "灵光", "Alipay"],
        "Elastic": ["Elastic", "Agent2Agent", "A2A"],
        "MOSS": ["MOSS", "MOSS-Speech"],
        "Grok": ["Grok", "xAI"],
        "LangChain": ["LangChain", "langchain"],
        "LangGraph": ["LangGraph", "langgraph"],
        "CrewAI": ["CrewAI", "crewai"],
        "AgentScope": ["AgentScope", "agentscope"],
        "AutoGen": ["AutoGen", "autogen"],
    }
    
    def _extract_products_keywords(title: str, summary: str = "") -> List[str]:
        """基于关键词提取产品"""
        found_products = set()
        text = (title + " " + summary).lower()
        
        for product, keywords in product_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    found_products.add(product)
                    break  # 找到该产品的一个关键词即可
        
        # 返回前2个主要产品
        return list(found_products)[:2]
    
    # 如果使用LLM，对重要资讯增强产品识别
    if use_llm:
        from common.llm import LLMClient
        client = LLMClient()
        if client.api_key:
            try:
                # 识别重要资讯
                important_news = identify_important_news(news[:30], logger, use_llm=True)
                important_titles = {n.title for n in important_news}
                
                # 对重要资讯使用LLM提取
                for n in news[:30]:
                    if n.title in important_titles:
                        summary = ""
                        if n.tags:
                            for tag in n.tags:
                                if tag.startswith("摘要: "):
                                    summary = tag.replace("摘要: ", "").strip()
                                    break
                        
                        prompt = f"从以下资讯中提取涉及的产品或公司名称（最多2个主要产品）：\n标题: {n.title}\n摘要: {summary[:200] if summary else '无'}\n\n返回JSON格式：{{\"products\": [\"产品1\", \"产品2\"]}}"
                        messages = [
                            {"role": "system", "content": "你是技术资讯分析师，请准确提取产品名称。"},
                            {"role": "user", "content": prompt},
                        ]
                        try:
                            result = client.chat_json(messages=messages, model=None)
                            products = result.get("products", [])
                            if isinstance(products, list):
                                title_to_products[n.title] = products[:2]
                                continue
                        except Exception:
                            pass  # 回退到关键词方法
                
            except Exception as e:
                logger.debug("LLM产品提取失败，使用关键词方法: %s", e)
    
    # 对所有资讯使用关键词提取
    for n in news:
        if n.title not in title_to_products:
            summary = ""
            if n.tags:
                for tag in n.tags:
                    if tag.startswith("摘要: "):
                        summary = tag.replace("摘要: ", "").strip()
                        break
            products = _extract_products_keywords(n.title, summary)
            if products:
                title_to_products[n.title] = products
    
    return title_to_products


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

