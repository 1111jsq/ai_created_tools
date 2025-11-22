from __future__ import annotations
import os
from typing import Optional
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI
from openai._exceptions import APIError, APITimeoutError, RateLimitError

from config import DEEPSEEK_CONFIG, LLM_CONFIG


class DeepSeekClient:
    """DeepSeek LLM 客户端包装，带超时与重试。"""

    def __init__(self, model: Optional[str] = None) -> None:
        api_key = DEEPSEEK_CONFIG.get('api_key')
        base_url = DEEPSEEK_CONFIG.get('base_url')
        self.model = model or DEEPSEEK_CONFIG.get('default_model', 'deepseek-chat')
        self._available = bool(api_key)
        self.client = OpenAI(api_key=api_key, base_url=base_url) if self._available else None

    def available(self) -> bool:
        return self._available

    @retry(reraise=True,
           stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=1, max=10),
           retry=retry_if_exception_type((APIError, APITimeoutError, RateLimitError)))
    def summarize(self, content: str, system_prompt: Optional[str] = None) -> str:
        if not self._available:
            return ""
        system_msg = system_prompt or "这是langchain在github中的历史版本页面，请帮我输出当前页面都做了那些变更，我主要关注是否引入新特性，是有有特性发生变化，修复的bug不是我关心的内容，内容要求有版本，并且要求根据重要性，进行高中低标记,要求表述简洁一些，中文回复。"
        timeout = LLM_CONFIG.get('timeout', 60)
        temperature = LLM_CONFIG.get('temperature', 0.7)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"请整理以下 GitHub Release 页面内容：\n\n{content}"},
            ],
            temperature=temperature,
            timeout=timeout,
        )
        return resp.choices[0].message.content or ""

    def split_text(self, text: str, chunk_chars: int, overlap: int) -> list[str]:
        """保留兼容接口，但不再使用字符窗口；具体切分由 split_by_versions 完成。"""
        return self.split_by_versions(text, versions_per_chunk=int(LLM_CONFIG.get('versions_per_chunk', 20)))

    def split_by_versions(self, text: str, versions_per_chunk: int) -> list[str]:
        """按 Markdown 的 "## " 作为版本边界，将每20个版本合并为一个文本块。

        规则：
        - 认为每个以 "## " 开头的标题是一版
        - 从该标题行开始，直到下一个 "## " 标题或文末结束，作为一个版本段
        - 将版本段按 versions_per_chunk 分批合并
        """
        if not text:
            return []
        # 匹配二级标题行的所有位置
        pattern = re.compile(r"^##\s+\d+\.\s?.+$", re.M)
        matches = list(pattern.finditer(text))
        if not matches:
            return [text]
        # 提取每个版本段
        version_sections: list[str] = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            version_sections.append(text[start:end].strip())
        if versions_per_chunk <= 0:
            versions_per_chunk = 20
        print(f"version_sections len is:{len(version_sections)}")
        # 合并为块
        chunks: list[str] = []
        for i in range(0, len(version_sections), versions_per_chunk):
            group = version_sections[i:i + versions_per_chunk]
            # 为每个块添加头部，方便 LLM 理解
            block = [f"# 版本块 {i // versions_per_chunk + 1}", ""] + group
            chunks.append("\n\n".join(block))
        return chunks

    def summarize_long(self, content: str, system_prompt: Optional[str] = None) -> list[str]:
        """对超长文本进行分段总结，返回各段摘要，调用方可再汇总。"""
        # 可选预筛选：默认关闭，避免漏掉版本
        if not self._available:
            return []
        if bool(LLM_CONFIG.get('pre_filter', False)):
            content = self.extract_relevant_sections(content)
        chunks = self.split_by_versions(content, versions_per_chunk=int(LLM_CONFIG.get('versions_per_chunk', 20)))
        results: list[str] = []
        for idx, ch in enumerate(chunks, start=1):
            prefix = f"(第{idx}/{len(chunks)}段)\n"
            summary = self.summarize(prefix + ch, system_prompt=system_prompt)
            results.append(summary)
        return results

    def summarize_aggregate(self, chunk_summaries: list[str]) -> str:
        """对分段摘要进行总览汇总。"""
        if not self._available or not chunk_summaries:
            return ""
        content = "\n\n".join(f"[段{idx}]\n{txt}" for idx, txt in enumerate(chunk_summaries, start=1))
        return self.summarize(
            content,
            system_prompt=(
                "你将看到多段分段摘要，请汇总为一份最终总结。要求：\n"
                "- 仅保留关键新增特性与变更，按重要性标记高/中/低；\n"
                "- 合并重复信息，去除实现细节与无关修复；\n"
                "- 结构清晰，列表输出；\n"
                "- 中文精简表述。"
            ),
        )

    def extract_relevant_sections(self, text: str) -> str:
        """从 Markdown 中提取与新增特性/变更相关的段落，减少无关内容。

        规则：保留标题含有以下关键词的段落直到下一标题：
        Feature, Added, New, Change, Breaking, Enhancement, Improvement, Deprecation
        """
        if not text:
            return text
        pattern = re.compile(r"^#{1,6}\s+.*$", re.M)
        headings = list(pattern.finditer(text))
        if not headings:
            return text
        keep_keywords = (
            "feature", "added", "new", "change", "breaking", "enhancement", "improvement", "deprecation"
        )
        kept_chunks: list[str] = []
        for i, h in enumerate(headings):
            title = h.group(0).lower()
            if any(k in title for k in keep_keywords):
                start = h.start()
                end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
                kept_chunks.append(text[start:end])
        if kept_chunks:
            return "\n\n".join(kept_chunks)
        return text


