import os
from dotenv import load_dotenv
from openai import OpenAI
from .models import PresentationRequest

# Load environment variables
load_dotenv()

class LLMService:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.model = model or os.getenv("LLM_MODEL", "deepseek-chat")
        
        if not self.api_key:
            # For local testing without key, or rely on env
            pass 
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def analyze_data(self, text: str) -> PresentationRequest:
        """
        Analyzes natural language text and extracts structured data for a presentation.
        """
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

        try:
            # DeepSeek and others may not support beta.parse / structured outputs fully
            # So we use standard JSON mode
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
            
            content = completion.choices[0].message.content
            return PresentationRequest.model_validate_json(content)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            raise e

