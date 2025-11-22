from __future__ import annotations

from common.llm import LLMClient
from .models import PresentationRequest


class LLMService:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.client = LLMClient(api_key=api_key, base_url=base_url, model=model)

    def analyze_data(self, text: str) -> PresentationRequest:
        system_prompt = (
            "You are an expert data analyst and presentation designer. "
            "Your goal is to extract data from the user's description and structure it for a PowerPoint slide. "
            "Identify the most suitable chart type (BAR, LINE, PIE, SCATTER) based on the data trends. "
            "Summarize the key insight in the summary field.\n\n"
            "IMPORTANT: Return ONLY valid JSON matching this structure:\n"
            "{\n"
            '  "slide_title": "string",\n'
            '  "summary": "string",\n'
            '  "chart_type": "BAR" | "LINE" | "PIE" | "SCATTER",\n'
            '  "data": {\n'
            '    "title": "string",\n'
            '    "categories": ["string"],\n'
            '    "series": [{"name": "string", "values": [number]}],\n'
            '    "x_axis_label": "string (optional)",\n'
            '    "y_axis_label": "string (optional)"\n'
            '  }\n'
            "}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        data = self.client.chat_json(messages)
        # 兼容 raw 返回
        if "raw" in data and isinstance(data["raw"], str):
            return PresentationRequest.model_validate_json(data["raw"])
        return PresentationRequest.model_validate(data)
